import pygame
from typing import Optional, TYPE_CHECKING, Protocol

from ui.hud import draw_perk_choice_overlay
from systems.party import get_companion, recalc_companion_stats_for_level
from systems import perks as perk_system

if TYPE_CHECKING:
    from engine.game import Game


class BaseScreen(Protocol):
    """
    Minimal protocol for a UI 'screen' or overlay.

    We keep it deliberately tiny:
    - handle_event(game, event): process input.
    - draw(game): draw on top of whatever the Game already rendered.
    """

    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        ...

    def draw(self, game: "Game") -> None:
        ...


class PerkChoiceScreen:
    """
    Thin helper around the perk-choice overlay.

    All persistent state (pending choices, queues, hero/companion stats)
    still lives on the Game instance. This class only handles input and
    drawing for the perk selection UI.
    """

    # ---- Queue management -------------------------------------------------

    def enqueue_perk_choice(
        self,
        game: "Game",
        owner: str,
        companion_index: Optional[int] = None,
    ) -> None:
        """
        Push a pending perk-choice owner into the game's queue.

        owner: "hero" or "companion".
        """
        if owner not in ("hero", "companion"):
            return
        game.perk_choice_queue.append((owner, companion_index))

    def start_next_perk_choice(self, game: "Game") -> None:
        """
        Pop the next entry from game.perk_choice_queue and open the overlay
        if it yields any perk options. If the queue is empty or no options
        exist, we return to exploration.
        """
        # Reset current owner + choices.
        game.pending_perk_choices = []
        game.perk_choice_owner = None
        game.perk_choice_companion_index = None

        while game.perk_choice_queue:
            owner, companion_index = game.perk_choice_queue.pop(0)

            if owner == "hero":
                choices = perk_system.pick_perk_choices(
                    game.hero_stats, max_choices=3
                )
                target_label = "Hero"
            elif (
                owner == "companion"
                and companion_index is not None
                and 0 <= companion_index < len(game.party)
            ):
                comp_state = game.party[companion_index]
                # Use the same perk system but operating on the companion state.
                choices = perk_system.pick_perk_choices(
                    comp_state, max_choices=3
                )

                # Try to build a friendly label for the overlay
                display_name = getattr(comp_state, "name_override", None)
                if not display_name:
                    display_name = getattr(comp_state, "name", None)
                if not display_name:
                    try:
                        template_for_name = get_companion(
                            comp_state.template_id
                        )
                    except Exception:
                        template_for_name = None
                    if template_for_name is not None:
                        display_name = getattr(
                            template_for_name, "name", None
                        )
                if not display_name:
                    display_name = f"Companion {companion_index + 1}"

                target_label = display_name
            else:
                # Invalid entry, move on.
                continue

            if not choices:
                # No valid perks for this owner; skip to the next entry.
                continue

            # Activate this owner + choices.
            game.pending_perk_choices = choices
            game.perk_choice_owner = owner
            game.perk_choice_companion_index = companion_index

            # Switch to perk-choice overlay.
            game.enter_perk_choice_mode()

            # Optional: a message so the log shows whose perk this is.
            if game.perk_choice_owner == "hero":
                game.add_message(
                    "Level up! Choose a new perk for your hero."
                )
            else:
                game.add_message(
                    f"{target_label} reached a new level! Choose a new perk."
                )

            return

        # If we ran out of entries, make sure we are back in exploration mode
        # (unless some other mode has taken over).
        if game.mode == "perk_choice":
            game.enter_exploration_mode()

    # ---- Event handling ---------------------------------------------------

    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        """Handle key input while the perk-choice overlay is open."""
        if event.type != pygame.KEYDOWN:
            return

        # Cancel perk selection
        if event.key == pygame.K_ESCAPE:
            # Clear current choices and queue; return to exploration.
            game.pending_perk_choices = []
            game.perk_choice_queue = []
            game.perk_choice_owner = None
            game.perk_choice_companion_index = None
            # Avoid importing GameMode here to prevent cycles; use the API.
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

        # Apply perk to the correct owner.
        if game.perk_choice_owner == "hero":
            # Perk.apply handles adding its id to hero_stats.perks and modifying stats.
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

                # Record perk on the companion.
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

        # Clear the current choice set and continue with the next queued one, if any.
        game.pending_perk_choices = []
        game.perk_choice_owner = None
        game.perk_choice_companion_index = None

        if game.perk_choice_queue:
            # Start the next queued perk-choice.
            self.start_next_perk_choice(game)
        else:
            # No more queued level-ups; return to exploration.
            game.enter_exploration_mode()

    # ---- Drawing ----------------------------------------------------------

    def draw(self, game: "Game") -> None:
        """
        Draw the perk-choice overlay on top of the already-rendered world.

        Game is responsible for drawing exploration / battle first;
        this only adds the UI overlay.
        """
        draw_perk_choice_overlay(game)
