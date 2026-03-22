using UnrealBuildTool;
using System.Collections.Generic;

public class SplatPlugin : ModuleRules
{
    public SplatPlugin(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });

        PrivateDependencyModuleNames.AddRange(new string[] { });
    }
}
