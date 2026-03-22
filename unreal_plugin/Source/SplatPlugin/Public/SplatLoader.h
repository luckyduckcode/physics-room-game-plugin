// Minimal header for a runtime splat loader (non-functional stub)
#pragma once

#include "CoreMinimal.h"
#include "UObject/ObjectMacros.h"
#include "UObject/ScriptMacros.h"

/**
 * USplatLoader
 * Runtime stub: implement PLY parsing and instanced mesh/particle creation here.
 */
UCLASS(Blueprintable, ClassGroup=(Rendering))
class USplatLoader : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Splat")
    void LoadFromPly(const FString& Path);
};
