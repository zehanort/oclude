; ModuleID = 'tests/toy_kernels/stress.cl'
source_filename = "tests/toy_kernels/stress.cl"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local i32 @divRndUp(i32 %n, i32 %d) #0 {
entry:
  %n.addr = alloca i32, align 4
  %d.addr = alloca i32, align 4
  store i32 %n, i32* %n.addr, align 4
  store i32 %d, i32* %d.addr, align 4
  %0 = load i32, i32* %n.addr, align 4
  %1 = load i32, i32* %d.addr, align 4
  %div = sdiv i32 %0, %1
  %2 = load i32, i32* %n.addr, align 4
  %3 = load i32, i32* %d.addr, align 4
  %rem = srem i32 %2, %3
  %tobool = icmp ne i32 %rem, 0
  %4 = zext i1 %tobool to i64
  %cond = select i1 %tobool, i32 1, i32 0
  %add = add nsw i32 %div, %cond
  ret i32 %add
}

attributes #0 = { convergent noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!opencl.ocl.version = !{!1}
!llvm.ident = !{!2}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 2, i32 0}
!2 = !{!"clang version 10.0.0 (https://github.com/llvm/llvm-project.git 9cdcd81d3f2e9c1c9ae1e054e24668d46bc08bfb)"}
