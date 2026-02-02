"""
Seven-Point Story Structure (Dan Wells Method).

A plot-driven structure focusing on key turning points, popularized by Dan Wells
at the 2013 Life, the Universe, & Everything conference. Based on the Star Trek
Roleplaying Game Narrator's Guide structure.

=== KEY METHODOLOGY: WORK BACKWARDS ===

The critical insight is to plot in this order (NOT chronological):
1. RESOLUTION  - Know your ending first
2. HOOK        - Create the OPPOSITE starting state
3. MIDPOINT    - The pivot point between them
4. PLOT TURN 1 - Bridge from Hook to Midpoint
5. PLOT TURN 2 - Bridge from Midpoint to Resolution
6. PINCH 1     - Pressure between Plot Turn 1 and Midpoint
7. PINCH 2     - Pressure between Midpoint and Plot Turn 2

=== SYMMETRY PRINCIPLE ===

The structure creates symmetry:
- Hook <-> Resolution: Opposite states (weak->strong, alone->loved, etc.)
- Plot Turn 1 <-> Plot Turn 2: Entry and exit bridges
- Pinch Point 1 <-> Pinch Point 2: Escalating pressure points
- Midpoint: The central pivot

=== THE "OPPOSITE STATE" RULE ===

If your character ends STRONG, they must start WEAK.
If they end LOVED, they must start ALONE.
If they end CONFIDENT, they must start UNCERTAIN.
The story is the journey between these opposite states.

Sources:
- Dan Wells' YouTube series (5 parts, ~10 min each)
- https://reedsy.com/blog/guide/story-structure/seven-point-story-structure/
- https://livingwriter.com/blog/dan-wells-seven-point-story-structure/
- https://kindlepreneur.com/7-point-story/
"""

from src.story_structures.base_structure import BaseStructure, Beat


class SevenPointStructure(BaseStructure):
    """Seven-Point Story Structure for plot-driven narratives.

    Best suited for:
    - Thriller/suspense stories
    - Mystery plots
    - Action-adventure
    - Any story with clear external conflict

    Key feature: Work backwards from resolution to create tight, purposeful plots.
    """

    name = "Seven-Point Story Structure"
    short_name = "seven_point"
    source = "Dan Wells / Star Trek RPG Narrator's Guide"
    num_acts = 3

    # Recommended plotting order (NOT chronological!)
    # This is the Dan Wells method - start with the end
    plotting_order = [
        "resolution",      # 1. Know your ending first
        "hook",            # 2. Create the OPPOSITE starting state
        "midpoint",        # 3. The pivot point
        "plot_turn_1",     # 4. Bridge: Hook -> Midpoint
        "plot_turn_2",     # 5. Bridge: Midpoint -> Resolution
        "pinch_point_1",   # 6. Pressure before midpoint
        "pinch_point_2",   # 7. Pressure after midpoint
    ]

    # Beats in CHRONOLOGICAL order (how they appear in the story)
    beats = [
        Beat(
            "hook",
            "Protagonist's 'BEFORE' state - must be OPPOSITE of resolution. "
            "Establish what's missing, broken, or incomplete. Show their flaw, "
            "weakness, or unfulfilled need. This is who they are BEFORE transformation.",
            act=1
        ),
        Beat(
            "plot_turn_1",
            "The INCITING INCIDENT that forces protagonist into the story. "
            "Something disrupts their world - a call to adventure, new information, "
            "or event that changes everything. They can no longer stay in the hook state.",
            act=1
        ),
        Beat(
            "pinch_point_1",
            "First major PRESSURE from antagonist/conflict. Stakes become real. "
            "The antagonist shows their power, or the conflict proves itself serious. "
            "Forces protagonist to react and raises tension.",
            act=2
        ),
        Beat(
            "midpoint",
            "The PIVOT: protagonist shifts from REACTION to ACTION. "
            "Before midpoint: things happen TO them. After midpoint: they MAKE things happen. "
            "Often involves gaining crucial knowledge, making a decision, or committing fully.",
            act=2
        ),
        Beat(
            "pinch_point_2",
            "DARKEST MOMENT - maximum pressure, all seems lost. "
            "Protagonist loses something important (mentor dies, ally betrays, plan fails). "
            "This is the 'jaws of defeat' moment that makes victory meaningful.",
            act=2
        ),
        Beat(
            "plot_turn_2",
            "The FINAL PIECE - discovery that enables victory. "
            "Protagonist gets the last information, tool, or insight needed. "
            "The path to resolution becomes clear. Often ties back to earlier setup.",
            act=3
        ),
        Beat(
            "resolution",
            "Protagonist's 'AFTER' state - OPPOSITE of hook. "
            "The transformation is complete. Story question answered. "
            "They have become who they needed to be to succeed.",
            act=3
        ),
    ]

    outline_prompt = """
Structure this story using DAN WELLS' SEVEN-POINT STRUCTURE.

## CRITICAL: PLOT IN THIS ORDER (not chronologically!)

**Step 1 - RESOLUTION**: Define the ending first.
- How does the story end?
- What state is the protagonist in?
- What have they become/achieved/lost?

**Step 2 - HOOK**: Create the OPPOSITE starting state.
- If they end strong, they start weak
- If they end loved, they start alone
- If they end confident, they start uncertain
- The story is the journey between these opposites

**Step 3 - MIDPOINT**: The pivot between hook and resolution.
- Where protagonist shifts from REACTIVE to PROACTIVE
- Before: things happen TO them
- After: they MAKE things happen
- Often involves a key realization or decision

**Step 4 - PLOT TURN 1**: Bridge from Hook to Midpoint.
- The inciting incident
- Forces protagonist out of their comfort zone
- Sets them on the path toward midpoint

**Step 5 - PLOT TURN 2**: Bridge from Midpoint to Resolution.
- The final piece of the puzzle
- Gives protagonist what they need to win
- Often ties back to earlier setup

**Step 6 - PINCH POINT 1**: Pressure between Plot Turn 1 and Midpoint.
- First major obstacle/antagonist pressure
- Raises stakes
- Shows protagonist what they're up against

**Step 7 - PINCH POINT 2**: Pressure between Midpoint and Plot Turn 2.
- Darkest moment - all seems lost
- Protagonist loses something important
- Creates "jaws of defeat" before victory

## CHRONOLOGICAL ORDER (how beats appear in story):

1. **HOOK** (~10% mark)
   - Establish protagonist in "before" state
   - Show what's missing/broken in their life
   - Create sympathy and interest

2. **PLOT TURN 1** (~20% mark)
   - World-changing event or discovery
   - Protagonist forced into the story
   - No going back to normal

3. **PINCH POINT 1** (~35% mark)
   - Antagonist/conflict applies pressure
   - Stakes become real
   - Protagonist must react

4. **MIDPOINT** (~50% mark)
   - The pivot point
   - Protagonist takes charge
   - Shifts from reactive to proactive

5. **PINCH POINT 2** (~70% mark)
   - Everything falls apart
   - Darkest moment
   - All hope seems lost

6. **PLOT TURN 2** (~85% mark)
   - Final revelation/discovery
   - Path to victory revealed
   - Protagonist has what they need

7. **RESOLUTION** (~100% mark)
   - Final confrontation
   - Protagonist in "after" state
   - Story question answered

## Scene Distribution:
- Act 1 (Hook + Plot Turn 1): ~25% of scenes
- Act 2 (Pinch 1 + Midpoint + Pinch 2): ~50% of scenes
- Act 3 (Plot Turn 2 + Resolution): ~25% of scenes

## KEY PRINCIPLES:
- The midpoint is where passive becomes active
- Pinch points apply PRESSURE - they're not just "bad things happen"
- Plot turns are BRIDGES - they connect major sections
- Resolution should feel earned because of the journey
"""

    def get_scene_distribution(self, total_scenes: int) -> dict[str, list[int]]:
        """Custom distribution matching 7-point structure (25/50/25)."""
        setup_count = max(1, int(total_scenes * 0.25))
        resolution_count = max(1, int(total_scenes * 0.25))
        middle_count = total_scenes - setup_count - resolution_count

        return {
            "act_1": list(range(0, setup_count)),
            "act_2": list(range(setup_count, setup_count + middle_count)),
            "act_3": list(range(setup_count + middle_count, total_scenes)),
        }

    def get_plotting_guide(self) -> str:
        """Returns step-by-step guide for plotting in Dan Wells order.

        This guide walks through how to develop a story using the
        backwards-from-resolution methodology.
        """
        return """
## DAN WELLS 7-POINT PLOTTING GUIDE

### Step 1: Define Your RESOLUTION
Ask yourself:
- How does this story end?
- What final state is my protagonist in?
- What transformation has occurred?

Write a one-sentence resolution:
"[Character] [achieves/becomes/defeats] [goal/state/antagonist]"

Example: "Katniss wins the Hunger Games and exposes the Capitol's cruelty"

---

### Step 2: Create the HOOK (Opposite of Resolution)
The hook must be the OPPOSITE of your resolution.

Resolution -> Hook mapping:
- Wins -> Starts as loser/underdog
- Confident -> Starts uncertain/fearful
- Loved -> Starts alone/rejected
- Powerful -> Starts powerless
- Free -> Starts trapped
- Wise -> Starts naive

Write your hook:
"[Character] is [opposite state] because [situation/flaw]"

Example: "Katniss lives in poverty, struggling to feed her family in an oppressive district"

---

### Step 3: Define the MIDPOINT (The Pivot)
The midpoint is where your protagonist changes from REACTIVE to PROACTIVE.

Before midpoint: Things happen TO them. They respond, react, survive.
After midpoint: They MAKE things happen. They plan, act, attack.

This often involves:
- A key realization ("I've been wrong about X")
- A firm decision ("I will do X no matter the cost")
- Gaining crucial information ("Now I understand how to beat them")

Write your midpoint:
"[Character] decides/realizes [key insight] and commits to [proactive goal]"

Example: "Katniss decides to play the games her way, defying the Capitol's narrative"

---

### Step 4: Bridge with PLOT TURN 1 (Hook -> Midpoint)
Plot Turn 1 is the inciting incident that:
- Disrupts the hook state
- Forces protagonist into the story
- Sets them on the path toward midpoint

This is NOT optional for the protagonist - something compels them to act.

Write your Plot Turn 1:
"[Event/Discovery] forces [Character] to [leave comfort zone]"

Example: "Katniss volunteers as tribute to save her sister Prim"

---

### Step 5: Bridge with PLOT TURN 2 (Midpoint -> Resolution)
Plot Turn 2 gives the protagonist the final piece needed to succeed.

This could be:
- A piece of information
- A weapon or tool
- An ally's help
- An internal realization
- A discovered weakness in the antagonist

Often ties back to earlier setup (Chekhov's gun).

Write your Plot Turn 2:
"[Character] [discovers/receives/realizes] [the key to victory]"

Example: "Katniss realizes she can threaten mutual suicide to force the Capitol's hand"

---

### Step 6: Add PINCH POINT 1 (Pressure after Plot Turn 1)
Pinch Point 1 applies pressure and raises stakes:
- Shows the antagonist's power
- Proves the conflict is serious
- Forces the protagonist to react

The protagonist is still REACTIVE here (before midpoint).

Write your Pinch Point 1:
"[Antagonist/Conflict] demonstrates power by [threat/action], forcing [Character] to [react]"

Example: "Katniss sees the deadly skills of career tributes and realizes how outmatched she is"

---

### Step 7: Add PINCH POINT 2 (Darkest Moment)
Pinch Point 2 is the "jaws of defeat" - the darkest moment:
- Something important is lost (ally, hope, advantage)
- All seems lost
- Victory appears impossible

This makes the eventual victory meaningful and earned.

Write your Pinch Point 2:
"[Character] loses [important thing], and [antagonist] appears to have won"

Example: "The Capitol announces only one tribute can survive, betraying Katniss and Peeta's alliance"

---

### FINAL CHECK: Does Your Plot Flow?

Hook -> (Plot Turn 1) -> Pinch 1 -> MIDPOINT -> Pinch 2 -> (Plot Turn 2) -> Resolution

- [ ] Hook and Resolution are OPPOSITES
- [ ] Plot Turn 1 forces protagonist into the story
- [ ] Pinch 1 applies pressure BEFORE midpoint
- [ ] Midpoint shifts protagonist from REACTIVE to PROACTIVE
- [ ] Pinch 2 is the DARKEST moment
- [ ] Plot Turn 2 provides the key to victory
- [ ] Resolution shows completed transformation
"""

    def get_example_breakdown(self, example: str = "hunger_games") -> str:
        """Returns beat-by-beat breakdown of example story.

        Args:
            example: Which example to show. Options:
                     'hunger_games', 'harry_potter', 'star_wars'
        """
        examples = {
            "hunger_games": """
## THE HUNGER GAMES - 7-Point Breakdown

**HOOK**: Katniss lives in poverty in District 12, struggling to feed her
family by illegal hunting. She's powerless under Capitol oppression.
> State: Powerless, surviving, alone

**PLOT TURN 1**: At the reaping, Prim's name is called. Katniss volunteers
as tribute to save her sister, entering the Games.
> Forced into the story by love for her sister

**PINCH POINT 1**: During training and the parade, Katniss sees the brutal
skills of Career tributes. She scores an 11, making her a target.
> Stakes raised: She's outmatched AND hunted

**MIDPOINT**: After Rue's death, Katniss covers her body with flowers in
an act of defiance. She commits to playing the Games HER way.
> Shift: From surviving TO actively defying the Capitol

**PINCH POINT 2**: The Gamemakers announce rule change allowing two
District partners to win together. Katniss and Peeta team up. Then the
Capitol REVOKES the rule - only one can survive.
> Darkest moment: Betrayed, must kill Peeta or die

**PLOT TURN 2**: Katniss realizes she can THREATEN mutual suicide with
the poisonous berries - the Capitol needs a victor for their spectacle.
> Final piece: Understanding the Capitol's weakness

**RESOLUTION**: Capitol backs down. Both survive. Katniss has gone from
powerless victim to symbol of rebellion.
> State: Powerful, defiant, symbol of hope
""",
            "harry_potter": """
## HARRY POTTER AND THE SORCERER'S STONE - 7-Point Breakdown

**HOOK**: Harry lives miserably under the stairs at the Dursleys, unloved
and treated as a burden. He has no identity, no belonging.
> State: Unloved, powerless, without identity

**PLOT TURN 1**: Hagrid delivers the Hogwarts letter and reveals Harry is
a wizard - famous in a world he never knew existed.
> Forced into the story by his true identity revealed

**PINCH POINT 1**: Harry learns someone tried to steal from Gringotts,
and Snape seems connected to Voldemort. Danger lurks at Hogwarts.
> Stakes raised: The magical world has real threats

**MIDPOINT**: Harry discovers the Sorcerer's Stone is at Hogwarts and
realizes Snape is trying to steal it. He decides to stop the theft.
> Shift: From learning magic TO actively protecting the Stone

**PINCH POINT 2**: Harry, Ron, and Hermione face the trials alone.
Ron is injured. Hermione can't continue. Harry must face the end alone.
> Darkest moment: Allies lost, must face evil alone

**PLOT TURN 2**: Harry discovers it's Quirrell (not Snape) and learns
Voldemort can't touch him because of his mother's love protection.
> Final piece: Love is his weapon against Voldemort

**RESOLUTION**: Harry defeats Quirrell/Voldemort. He's found family
in his friends, belonging at Hogwarts, and his true identity.
> State: Loved, powerful, knows who he is
""",
            "star_wars": """
## STAR WARS: A NEW HOPE - 7-Point Breakdown

**HOOK**: Luke Skywalker is a bored farm boy on a remote desert planet,
dreaming of adventure but stuck in mundane moisture farming.
> State: Trapped, purposeless, ordinary

**PLOT TURN 1**: Luke finds R2-D2's message from Princess Leia. Obi-Wan
reveals Luke's father was a Jedi and offers to train him.
→ Forced into the story by his true heritage revealed

**PINCH POINT 1**: Luke returns home to find his aunt and uncle murdered
by Imperial stormtroopers. He has nothing left to lose.
> Stakes raised: The Empire is ruthless, this is personal

**MIDPOINT**: Luke joins the Rebellion and commits to rescuing Princess
Leia from the Death Star. He actively chooses the fight.
> Shift: From running away TO fighting for the Rebellion

**PINCH POINT 2**: Obi-Wan sacrifices himself fighting Darth Vader.
Luke loses his mentor and nearly loses hope.
> Darkest moment: Guide gone, facing the Empire alone

**PLOT TURN 2**: Luke hears Obi-Wan's voice: "Use the Force, Luke."
He turns off his targeting computer and trusts in the Force.
> Final piece: Faith in the Force over technology

**RESOLUTION**: Luke destroys the Death Star, saves the Rebellion, and
becomes a hero. He's found purpose, family, and his destiny.
> State: Free, purposeful, a hero
"""
        }

        return examples.get(example, examples["hunger_games"])


# Singleton instance
seven_point_structure = SevenPointStructure()
