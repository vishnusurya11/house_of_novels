"""Quick test to verify import bug is fixed"""

from src.story_agents.interconnection_agents import PlotThreadAgent, CharacterArcAgent

print("Testing PlotThreadAgent import fix...")
agent = PlotThreadAgent()
print(f"✅ PlotThreadAgent created: {agent.name}")

print("\nTesting CharacterArcAgent import fix...")
agent2 = CharacterArcAgent()
print(f"✅ CharacterArcAgent created: {agent2.name}")

print("\n✅ ALL IMPORT BUGS FIXED!")
