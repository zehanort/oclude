; ModuleID = 'tests/toy_kernels/stress.cl'
source_filename = "tests/toy_kernels/stress.cl"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local float @dev_round_float(float %value) #0 {
entry:
  %retval = alloca float, align 4
  %value.addr = alloca float, align 4
  %newValue = alloca i32, align 4
  store float %value, float* %value.addr, align 4
  %0 = load float, float* %value.addr, align 4
  %conv = fptosi float %0 to i32
  store i32 %conv, i32* %newValue, align 4
  %1 = load float, float* %value.addr, align 4
  %2 = load i32, i32* %newValue, align 4
  %conv1 = sitofp i32 %2 to float
  %sub = fsub float %1, %conv1
  %cmp = fcmp olt float %sub, 5.000000e-01
  br i1 %cmp, label %if.then, label %if.else

if.then:                                          ; preds = %entry
  %3 = load i32, i32* %newValue, align 4
  %conv3 = sitofp i32 %3 to float
  store float %conv3, float* %retval, align 4
  br label %return

if.else:                                          ; preds = %entry
  %4 = load i32, i32* %newValue, align 4
  %inc = add nsw i32 %4, 1
  store i32 %inc, i32* %newValue, align 4
  %conv4 = sitofp i32 %4 to float
  store float %conv4, float* %retval, align 4
  br label %return

return:                                           ; preds = %if.else, %if.then
  %5 = load float, float* %retval, align 4
  ret float %5
}

attributes #0 = { convergent noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!opencl.ocl.version = !{!1}
!llvm.ident = !{!2}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 2, i32 0}
!2 = !{!"clang version 10.0.0 (https://github.com/llvm/llvm-project.git 9cdcd81d3f2e9c1c9ae1e054e24668d46bc08bfb)"}
