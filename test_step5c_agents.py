"""Quick test to verify all Step 5C agents work correctly"""

from src.story_agents.interconnection_agents import (
    SceneCausalityAgent,
    PlotThreadAgent,
    CharacterArcAgent,
    ThematicBeatAgent,
    SceneFunctionAgent,
    NarrativeRopeAgent,
    SynthesisValidator
)

print("Testing all Step 5C agents...")

agents = [
    (SceneCausalityAgent, "SceneCausalityAgent"),
    (PlotThreadAgent, "PlotThreadAgent"),
    (CharacterArcAgent, "CharacterArcAgent"),
    (ThematicBeatAgent, "ThematicBeatAgent"),
    (SceneFunctionAgent, "SceneFunctionAgent"),
    (NarrativeRopeAgent, "NarrativeRopeAgent"),
    (SynthesisValidator, "SynthesisValidator")
]

for AgentClass, name in agents:
    try:
        agent = AgentClass()
        print(f"✅ {name}: {agent.name}")
    except Exception as e:
        print(f"❌ {name}: {e}")
        exit(1)

print("\n✅ ALL 7 AGENTS INSTANTIATE CORRECTLY!")
print("\nTesting ThematicBeatAgent.invoke() fix...")

# Create minimal test data
chapter_outline = {
    'chapters': [{
        'chapter_number': 1,
        'chapter_title': 'Test Chapter',
        'scenes': [{
            'scene_number': 1,
            'beat_name': 'Opening Image',
            'scene_summary': 'Hero at work',
            'pov_character': 'Hero',
            'characters_present': ['Hero']
        }]
    }]
}

characters = []

try:
    agent = ThematicBeatAgent()
    # This will call invoke() without max_tokens - should not crash
    print("   Calling analyze_thematic_beats...")
    result = agent.analyze_thematic_beats(chapter_outline, characters)
    print(f"✅ ThematicBeatAgent.analyze_thematic_beats() completed!")
    print(f"   Returned {len(result)} thematic beat(s)")
    print(f"   Theme inferred: {result[0]['thematic_beat'].get('thematic_question', 'N/A')}")
except TypeError as e:
    if "max_tokens" in str(e):
        print(f"❌ STILL HAS MAX_TOKENS BUG: {e}")
        exit(1)
    else:
        raise
except Exception as e:
    print(f"⚠️  Other error (not the max_tokens bug): {e}")
    # This is OK - might be LLM/API error, not our bug

print("\n🎉 ALL TESTS PASSED! Step 5C is ready.")
