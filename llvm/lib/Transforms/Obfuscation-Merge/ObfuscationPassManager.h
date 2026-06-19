#ifndef OBFUSCATION_OBFUSCATIONPASSMANAGER_H
#define OBFUSCATION_OBFUSCATIONPASSMANAGER_H

#include "Flattening.h"
#include "IndirectBranch.h"
#include "IndirectCall.h"
#include "IndirectGlobalVariable.h"
#include "StringEncryption.h"
#include "ConstantIntEncryption.h"
#include "ConstantFPEncryption.h"
#include "Substitution.h"
#include "BogusControlFlow2.h"
#include "llvm/Passes/PassBuilder.h"

// Namespace
namespace llvm {
class ModulePass;
class PassRegistry;

ModulePass *createObfuscationPassManager();
void initializeObfuscationPassManagerPass(PassRegistry &Registry);

class ObfuscationPassManagerPass
    : public PassInfoMixin<ObfuscationPassManagerPass> {
public:
  PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
    ModulePass *OPM = createObfuscationPassManager();
    bool Changed = OPM->runOnModule(M);
    OPM->doFinalization(M);
    delete OPM;
    if (Changed) {
      return PreservedAnalyses::none();
    }
    return PreservedAnalyses::all();
  }
};

} // namespace llvm

#endif