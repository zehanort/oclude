; ModuleID = 'tests/toy_kernels/stress.cl'
source_filename = "tests/toy_kernels/stress.cl"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local i32 @fmod(i32 %x, i32 %y) #0 {
entry:
  %x.addr = alloca i32, align 4
  %y.addr = alloca i32, align 4
  store i32 %x, i32* %x.addr, align 4
  store i32 %y, i32* %y.addr, align 4
  %0 = load i32, i32* %x.addr, align 4
  %1 = load i32, i32* %y.addr, align 4
  %rem = srem i32 %0, %1
  ret i32 %rem
}
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local spir_kernel void @switchtest(i32* %dummy) #1 !kernel_arg_addr_space !3 !kernel_arg_access_qual !4 !kernel_arg_type !5 !kernel_arg_base_type !5 !kernel_arg_type_qual !6 {
entry:
  %dummy.addr = alloca i32*, align 8
  %I_app = alloca float, align 4
  %R_clamp = alloca float, align 4
  %timeinst = alloca i32, align 4
  %cycleLength = alloca i32, align 4
  %state = alloca i32, align 4
  %V_hold = alloca i32, align 4
  %V_test = alloca i32, align 4
  %V_clamp = alloca i32, align 4
  %d_initvalu_39 = alloca i32, align 4
  store i32* %dummy, i32** %dummy.addr, align 8
  store i32 2, i32* %timeinst, align 4
  store i32 2, i32* %cycleLength, align 4
  store i32 1, i32* %state, align 4
  %0 = load i32, i32* %state, align 4
  switch i32 %0, label %sw.epilog [
    i32 0, label %sw.bb
    i32 1, label %sw.bb1
    i32 2, label %sw.bb2
  ]

sw.bb:                                            ; preds = %entry
  store float 0.000000e+00, float* %I_app, align 4
  br label %sw.epilog

sw.bb1:                                           ; preds = %entry
  %1 = load i32, i32* %timeinst, align 4
  %2 = load i32, i32* %cycleLength, align 4
  %call = call i32 @fmod(i32 %1, i32 %2) #2
  %cmp = icmp sle i32 %call, 5
  br i1 %cmp, label %if.then, label %if.else

if.then:                                          ; preds = %sw.bb1
  store float 9.500000e+00, float* %I_app, align 4
  br label %if.end

if.else:                                          ; preds = %sw.bb1
  store float 0.000000e+00, float* %I_app, align 4
  br label %if.end

if.end:                                           ; preds = %if.else, %if.then
  br label %sw.epilog

sw.bb2:                                           ; preds = %entry
  store i32 -55, i32* %V_hold, align 4
  store i32 0, i32* %V_test, align 4
  %3 = load i32, i32* %timeinst, align 4
  %conv = sitofp i32 %3 to double
  %cmp3 = fcmp ogt double %conv, 5.000000e-01
  %conv4 = zext i1 %cmp3 to i32
  %4 = load i32, i32* %timeinst, align 4
  %conv5 = sitofp i32 %4 to double
  %cmp6 = fcmp olt double %conv5, 2.005000e+02
  %conv7 = zext i1 %cmp6 to i32
  %and = and i32 %conv4, %conv7
  %tobool = icmp ne i32 %and, 0
  br i1 %tobool, label %if.then8, label %if.else9

if.then8:                                         ; preds = %sw.bb2
  %5 = load i32, i32* %V_test, align 4
  store i32 %5, i32* %V_clamp, align 4
  br label %if.end10

if.else9:                                         ; preds = %sw.bb2
  %6 = load i32, i32* %V_hold, align 4
  store i32 %6, i32* %V_clamp, align 4
  br label %if.end10

if.end10:                                         ; preds = %if.else9, %if.then8
  store float 0x3FA47AE140000000, float* %R_clamp, align 4
  %7 = load i32, i32* %V_clamp, align 4
  %8 = load i32, i32* %d_initvalu_39, align 4
  %sub = sub nsw i32 %7, %8
  %conv11 = sitofp i32 %sub to float
  %9 = load float, float* %R_clamp, align 4
  %div = fdiv float %conv11, %9, !fpmath !7
  store float %div, float* %I_app, align 4
  br label %sw.epilog

sw.epilog:                                        ; preds = %entry, %if.end10, %if.end, %sw.bb
  store i32 42, i32* %state, align 4
  ret void
}

attributes #0 = { convergent noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { convergent noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "uniform-work-group-size"="false" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #2 = { convergent }

!llvm.module.flags = !{!0}
!opencl.ocl.version = !{!1}
!llvm.ident = !{!2}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 2, i32 0}
!2 = !{!"clang version 10.0.0 (https://github.com/llvm/llvm-project.git 9cdcd81d3f2e9c1c9ae1e054e24668d46bc08bfb)"}
!3 = !{i32 1}
!4 = !{!"none"}
!5 = !{!"int*"}
!6 = !{!""}
!7 = !{float 2.500000e+00}
