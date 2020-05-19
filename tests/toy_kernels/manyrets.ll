; ModuleID = 'tests/toy_kernels/stress.cl'
source_filename = "tests/toy_kernels/stress.cl"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local i32 @findIndexBin(float* %CDF, i32 %beginIndex, i32 %endIndex, float %value) #0 {
entry:
  %retval = alloca i32, align 4
  %CDF.addr = alloca float*, align 8
  %beginIndex.addr = alloca i32, align 4
  %endIndex.addr = alloca i32, align 4
  %value.addr = alloca float, align 4
  %middleIndex = alloca i32, align 4
  store float* %CDF, float** %CDF.addr, align 8
  store i32 %beginIndex, i32* %beginIndex.addr, align 4
  store i32 %endIndex, i32* %endIndex.addr, align 4
  store float %value, float* %value.addr, align 4
  %0 = load i32, i32* %endIndex.addr, align 4
  %1 = load i32, i32* %beginIndex.addr, align 4
  %cmp = icmp slt i32 %0, %1
  br i1 %cmp, label %if.then, label %if.end

if.then:                                          ; preds = %entry
  store i32 -1, i32* %retval, align 4
  br label %return

if.end:                                           ; preds = %entry
  br label %while.cond

while.cond:                                       ; preds = %if.end34, %if.end
  %2 = load i32, i32* %endIndex.addr, align 4
  %3 = load i32, i32* %beginIndex.addr, align 4
  %cmp1 = icmp sgt i32 %2, %3
  br i1 %cmp1, label %while.body, label %while.end35

while.body:                                       ; preds = %while.cond
  %4 = load i32, i32* %beginIndex.addr, align 4
  %5 = load i32, i32* %endIndex.addr, align 4
  %6 = load i32, i32* %beginIndex.addr, align 4
  %sub = sub nsw i32 %5, %6
  %div = sdiv i32 %sub, 2
  %add = add nsw i32 %4, %div
  store i32 %add, i32* %middleIndex, align 4
  %7 = load float*, float** %CDF.addr, align 8
  %8 = load i32, i32* %middleIndex, align 4
  %idxprom = sext i32 %8 to i64
  %arrayidx = getelementptr inbounds float, float* %7, i64 %idxprom
  %9 = load float, float* %arrayidx, align 4
  %10 = load float, float* %value.addr, align 4
  %cmp2 = fcmp oge float %9, %10
  br i1 %cmp2, label %if.then3, label %if.end26

if.then3:                                         ; preds = %while.body
  %11 = load i32, i32* %middleIndex, align 4
  %cmp4 = icmp eq i32 %11, 0
  br i1 %cmp4, label %if.then5, label %if.else

if.then5:                                         ; preds = %if.then3
  %12 = load i32, i32* %middleIndex, align 4
  store i32 %12, i32* %retval, align 4
  br label %return

if.else:                                          ; preds = %if.then3
  %13 = load float*, float** %CDF.addr, align 8
  %14 = load i32, i32* %middleIndex, align 4
  %sub6 = sub nsw i32 %14, 1
  %idxprom7 = sext i32 %sub6 to i64
  %arrayidx8 = getelementptr inbounds float, float* %13, i64 %idxprom7
  %15 = load float, float* %arrayidx8, align 4
  %16 = load float, float* %value.addr, align 4
  %cmp9 = fcmp olt float %15, %16
  br i1 %cmp9, label %if.then10, label %if.else11

if.then10:                                        ; preds = %if.else
  %17 = load i32, i32* %middleIndex, align 4
  store i32 %17, i32* %retval, align 4
  br label %return

if.else11:                                        ; preds = %if.else
  %18 = load float*, float** %CDF.addr, align 8
  %19 = load i32, i32* %middleIndex, align 4
  %sub12 = sub nsw i32 %19, 1
  %idxprom13 = sext i32 %sub12 to i64
  %arrayidx14 = getelementptr inbounds float, float* %18, i64 %idxprom13
  %20 = load float, float* %arrayidx14, align 4
  %21 = load float, float* %value.addr, align 4
  %cmp15 = fcmp oeq float %20, %21
  br i1 %cmp15, label %if.then16, label %if.end23

if.then16:                                        ; preds = %if.else11
  br label %while.cond17

while.cond17:                                     ; preds = %while.body22, %if.then16
  %22 = load float*, float** %CDF.addr, align 8
  %23 = load i32, i32* %middleIndex, align 4
  %idxprom18 = sext i32 %23 to i64
  %arrayidx19 = getelementptr inbounds float, float* %22, i64 %idxprom18
  %24 = load float, float* %arrayidx19, align 4
  %25 = load float, float* %value.addr, align 4
  %cmp20 = fcmp oeq float %24, %25
  br i1 %cmp20, label %land.rhs, label %land.end

land.rhs:                                         ; preds = %while.cond17
  %26 = load i32, i32* %middleIndex, align 4
  %cmp21 = icmp sge i32 %26, 0
  br label %land.end

land.end:                                         ; preds = %land.rhs, %while.cond17
  %27 = phi i1 [ false, %while.cond17 ], [ %cmp21, %land.rhs ]
  br i1 %27, label %while.body22, label %while.end

while.body22:                                     ; preds = %land.end
  %28 = load i32, i32* %middleIndex, align 4
  %dec = add nsw i32 %28, -1
  store i32 %dec, i32* %middleIndex, align 4
  br label %while.cond17

while.end:                                        ; preds = %land.end
  %29 = load i32, i32* %middleIndex, align 4
  %inc = add nsw i32 %29, 1
  store i32 %inc, i32* %middleIndex, align 4
  %30 = load i32, i32* %middleIndex, align 4
  store i32 %30, i32* %retval, align 4
  br label %return

if.end23:                                         ; preds = %if.else11
  br label %if.end24

if.end24:                                         ; preds = %if.end23
  br label %if.end25

if.end25:                                         ; preds = %if.end24
  br label %if.end26

if.end26:                                         ; preds = %if.end25, %while.body
  %31 = load float*, float** %CDF.addr, align 8
  %32 = load i32, i32* %middleIndex, align 4
  %idxprom27 = sext i32 %32 to i64
  %arrayidx28 = getelementptr inbounds float, float* %31, i64 %idxprom27
  %33 = load float, float* %arrayidx28, align 4
  %34 = load float, float* %value.addr, align 4
  %cmp29 = fcmp ogt float %33, %34
  br i1 %cmp29, label %if.then30, label %if.else32

if.then30:                                        ; preds = %if.end26
  %35 = load i32, i32* %middleIndex, align 4
  %sub31 = sub nsw i32 %35, 1
  store i32 %sub31, i32* %endIndex.addr, align 4
  br label %if.end34

if.else32:                                        ; preds = %if.end26
  %36 = load i32, i32* %middleIndex, align 4
  %add33 = add nsw i32 %36, 1
  store i32 %add33, i32* %beginIndex.addr, align 4
  br label %if.end34

if.end34:                                         ; preds = %if.else32, %if.then30
  br label %while.cond

while.end35:                                      ; preds = %while.cond
  store i32 -1, i32* %retval, align 4
  br label %return

return:                                           ; preds = %while.end35, %while.end, %if.then10, %if.then5, %if.then
  %37 = load i32, i32* %retval, align 4
  ret i32 %37
}

attributes #0 = { convergent noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!opencl.ocl.version = !{!1}
!llvm.ident = !{!2}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 2, i32 0}
!2 = !{!"clang version 10.0.0 (https://github.com/llvm/llvm-project.git 9cdcd81d3f2e9c1c9ae1e054e24668d46bc08bfb)"}
