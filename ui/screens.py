import pygame
from typing import Optional, Protocol, TYPE_CHECKING

from ui.hud import draw_perk_choice_overlay
from systems import perks as perk_system
from systems.party import get_companion, recalc_companion_stats_for_level

if TYPE_CHECKING:
    from engine.game import Game


class BaseScreen(Protocol):
    """
    Simple protocol for UI screens that can receive events and draw themselves.
    """
    def handle_event(self, game: "Game", event: pygame.event.Event) -> None: ...
    def draw(self, game: "Game") -> None: ...


class PerkChoiceScreen:
    """
    Thin helper around the perk-choice overlay.

    All persistent state (pending choices, queues, hero/companion stats)
    still lives on the Game instance. This class wires input + drawing and
    provides helpers for queueing and starting perk-choice flows.
    """

    # -------- Queue management helpers --------

    def enqueue_perk_choice(
        self,
        game: "Game",
        owner: str,
        companion_index: Optional[int] = None,
    ) -> None:
        """Push a perk choice for the given owner into the queue.

        Parameters
        ----------
        owner:
            Either "hero" or "companion".
        companion_index:
            Index into ``game.party`` when ``owner == "companion"``.
        """
        if owner not in ("hero", "companion"):
            return

        # The queue itself still lives on the Game.
        if not hasattr(game, "perk_choice_queue") or game.perk_choice_queue is None:
            game.perk_choice_queue = []  # type: ignore[attr-defined]

        game.perk_choice_queue.append((owner, companion_index))

    def start_next_perk_choice(self, game: "Game") -> None:
        """Pop the next queued perk owner and open the overlay if possible.

        Mirrors the old ``_start_next_perk_choice`` logic, but keeps it
        co-located with the perk-choice screen.
        """
        # Reset current owner + choices.
        game.pending_perk_choices = []
        game.perk_choice_owner = None
        game.perk_choice_companion_index = None

        # Defensive default if the queue is missing.
        queue = getattr(game, "perk_choice_queue", None)
        if queue is None:
            return

        from engine.game import GameMode  # local import to avoid cycles

        while queue:
            owner, companion_index = queue.pop(0)

            if owner == "hero":
                choices = perk_system.pick_perk_choices(game.hero_stats, max_choices=3)
                target_label = "Hero"

            elif (
                owner == "companion"
                and companion_index is not None
                and 0 <= companion_index < len(game.party)
            ):
                comp_state = game.party[companion_index]

                # Use the same perk system but operating on the companion state.
                choices = perk_system.pick_perk_choices(comp_state, max_choices=3)

                # Try to build a friendly label for the overlay.
                display_name = getattr(comp_state, "name_override", None)
                if not display_name:
                    display_name = getattr(comp_state, "name", None)
                if not display_name:
                    try:
                        template_for_name = get_companion(comp_state.template_id)
                    except Exception:
                        template_for_name = None
                    if template_for_name is not None:
                        display_name = getattr(template_for_name, "name", None)
                if not display_name:
                    display_name = f"Companion {companion_index + 1}"

                target_label = display_name
            else:
                # Invalid entry, move on.
                continue

            if not choices:
                # No valid perks for this owner; skip to the next entry in queue.
                continue

            # Activate this owner + choices.
            game.pending_perk_choices = choices
            game.perk_choice_owner = owner
            game.perk_choice_companion_index = companion_index

            # Switch to perk-choice overlay via the Game helper if it exists.
            if hasattr(game, "enter_perk_choice_mode"):
                game.enter_perk_choice_mode()
            else:
                game.mode = GameMode.PERK_CHOICE  # type: ignore[assignment]

            # Optional: a message so the log shows whose perk this is.
            if game.perk_choice_owner == "hero":
                game.add_message("Level up! Choose a new perk for your hero.")
            else:
                game.add_message(f"{target_label} reached a new level! Choose a new perk.")

            return

        # If we ran out of entries, make sure we are back in exploration mode
        # (unless some other mode has taken over).
        if getattr(game, "mode", None) == GameMode.PERK_CHOICE:
            if hasattr(game, "enter_exploration_mode"):
                game.enter_exploration_mode()
            else:
                game.mode = GameMode.EXPLORATION  # type: ignore[assignment]

    # -------- Input & drawing --------

    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        """Handle input while the perk-choice overlay is open."""
        if event.type != pygame.KEYDOWN:
            return

        # Cancel perk selection with ESC: clear everything and go back to exploration.
        if event.key == pygame.K_ESCAPE:
            game.pending_perk_choices = []
            game.perk_choice_queue = []
            game.perk_choice_owner = None
            game.perk_choice_companion_index = None
            game.enter_exploration_mode()
            return

        if not game.pending_perk_choices:
            return

        index: Optional[int] = None
        if event.key in (pygame.K_1, pygame.K_KP1):
            index = 0
        elif event.key in (pygame.K_2, pygame.K_KP2):
            index = 1
        elif event.key in (pygame.K_3, pygame.K_KP3):
            index = 2

        if index is None:
            return
        if not (0 <= index < len(game.pending_perk_choices)):
            return

        chosen = game.pending_perk_choices[index]

        # ----- Apply perk to the correct owner -----

        if game.perk_choice_owner == "hero":
            # Make sure we track owned perk ids on the hero.
            if not hasattr(game.hero_stats, "perks"):
                game.hero_stats.perks = []
            if chosen.id not in game.hero_stats.perks:
                game.hero_stats.perks.append(chosen.id)

            # Apply stat changes / granted skills to hero_stats.
            chosen.apply(game.hero_stats)

            # Mirror updated stats onto the player entity (no extra heal here).
            if game.player is not None:
                game.apply_hero_stats_to_player(full_heal=False)

            game.add_message(f"You learn a new perk: {chosen.name}")

        elif (
                game.perk_choice_owner == "companion"
                and game.perk_choice_companion_index is not None
        ):
            if 0 <= game.perk_choice_companion_index < len(game.party):
                comp_state = game.party[game.perk_choice_companion_index]

                # Record perk on the companion (data only).
                if chosen.id not in comp_state.perks:
                    comp_state.perks.append(chosen.id)

                # Recompute stats from template + level + perks.
                template = None
                try:
                    template = get_companion(comp_state.template_id)
                except Exception:
                    template = None

                if template is not None:
                    recalc_companion_stats_for_level(comp_state, template)

                # Build a safe display name
                display_name = getattr(comp_state, "name_override", None)
                if not display_name:
                    display_name = getattr(comp_state, "name", None)
                if not display_name and template is not None:
                    display_name = getattr(template, "name", None)
                if not display_name:
                    display_name = "Companion"

                game.add_message(
                    f"{display_name} learns a new perk: {chosen.name}"
                )

        # ----- Clear current choice and continue with queue -----

        game.pending_perk_choices = []
        game.perk_choice_owner = None
        game.perk_choice_companion_index = None

        if game.perk_choice_queue:
            # Start the next queued perk-choice.
            self.start_next_perk_choice(game)
        else:
            # No more queued level-ups; return to exploration.
            game.enter_exploration_mode()

    def draw(self, game: "Game") -> None:
        """
        Draw only the perk-choice overlay.

        Game.draw() is responsible for drawing the underlying world view
        (exploration / battle). This method just adds the perk UI on top.
        """
        draw_perk_choice_overlay(game)
