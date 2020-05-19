; ModuleID = 'tests/toy_kernels/stress.cl'
source_filename = "tests/toy_kernels/stress.cl"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

%opencl.image2d_ro_t = type opaque
%opencl.sampler_t = type opaque
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local float @tex1Dfetch(%opencl.image2d_ro_t* %img, i32 %index) #0 {
entry:
  %retval = alloca float, align 4
  %img.addr = alloca %opencl.image2d_ro_t*, align 8
  %index.addr = alloca i32, align 4
  %smp = alloca %opencl.sampler_t*, align 8
  %imgPos = alloca i32, align 4
  %coords = alloca <2 x i32>, align 8
  %temp = alloca <4 x float>, align 16
  %coerce = alloca <2 x i32>, align 8
  store %opencl.image2d_ro_t* %img, %opencl.image2d_ro_t** %img.addr, align 8
  store i32 %index, i32* %index.addr, align 4
  %0 = call %opencl.sampler_t* @__translate_sampler_initializer(i32 20)
  store %opencl.sampler_t* %0, %opencl.sampler_t** %smp, align 8
  %1 = load i32, i32* %index.addr, align 4
  %cmp = icmp slt i32 %1, 0
  br i1 %cmp, label %if.then, label %if.end

if.then:                                          ; preds = %entry
  store float 0.000000e+00, float* %retval, align 4
  br label %return

if.end:                                           ; preds = %entry
  %2 = load i32, i32* %index.addr, align 4
  %shr = ashr i32 %2, 2
  store i32 %shr, i32* %imgPos, align 4
  %3 = load i32, i32* %imgPos, align 4
  %shr1 = ashr i32 %3, 13
  %4 = load <2 x i32>, <2 x i32>* %coords, align 8
  %5 = insertelement <2 x i32> %4, i32 %shr1, i64 0
  store <2 x i32> %5, <2 x i32>* %coords, align 8
  %6 = load i32, i32* %imgPos, align 4
  %and = and i32 %6, 8191
  %7 = load <2 x i32>, <2 x i32>* %coords, align 8
  %8 = insertelement <2 x i32> %7, i32 %and, i64 1
  store <2 x i32> %8, <2 x i32>* %coords, align 8
  %9 = load %opencl.image2d_ro_t*, %opencl.image2d_ro_t** %img.addr, align 8
  %10 = load %opencl.sampler_t*, %opencl.sampler_t** %smp, align 8
  %11 = load <2 x i32>, <2 x i32>* %coords, align 8
  store <2 x i32> %11, <2 x i32>* %coerce, align 8
  %12 = bitcast <2 x i32>* %coerce to double*
  %13 = load double, double* %12, align 8
  %call = call <4 x float> @_Z11read_imagef14ocl_image2d_ro11ocl_samplerDv2_i(%opencl.image2d_ro_t* %9, %opencl.sampler_t* %10, double %13) #2
  store <4 x float> %call, <4 x float>* %temp, align 16
  %14 = load i32, i32* %index.addr, align 4
  %and2 = and i32 %14, 3
  store i32 %and2, i32* %imgPos, align 4
  %15 = load i32, i32* %imgPos, align 4
  %cmp3 = icmp slt i32 %15, 2
  br i1 %cmp3, label %if.then4, label %if.else7

if.then4:                                         ; preds = %if.end
  %16 = load i32, i32* %imgPos, align 4
  %cmp5 = icmp eq i32 %16, 0
  br i1 %cmp5, label %if.then6, label %if.else

if.then6:                                         ; preds = %if.then4
  %17 = load <4 x float>, <4 x float>* %temp, align 16
  %18 = extractelement <4 x float> %17, i64 0
  store float %18, float* %retval, align 4
  br label %return

if.else:                                          ; preds = %if.then4
  %19 = load <4 x float>, <4 x float>* %temp, align 16
  %20 = extractelement <4 x float> %19, i64 1
  store float %20, float* %retval, align 4
  br label %return

if.else7:                                         ; preds = %if.end
  %21 = load i32, i32* %imgPos, align 4
  %cmp8 = icmp eq i32 %21, 2
  br i1 %cmp8, label %if.then9, label %if.else10

if.then9:                                         ; preds = %if.else7
  %22 = load <4 x float>, <4 x float>* %temp, align 16
  %23 = extractelement <4 x float> %22, i64 2
  store float %23, float* %retval, align 4
  br label %return

if.else10:                                        ; preds = %if.else7
  %24 = load <4 x float>, <4 x float>* %temp, align 16
  %25 = extractelement <4 x float> %24, i64 3
  store float %25, float* %retval, align 4
  br label %return

return:                                           ; preds = %if.else10, %if.then9, %if.else, %if.then6, %if.then
  %26 = load float, float* %retval, align 4
  ret float %26
}
declare dso_local %opencl.sampler_t* @__translate_sampler_initializer(i32)
; Function Attrs: convergent nounwind readonly
declare dso_local <4 x float> @_Z11read_imagef14ocl_image2d_ro11ocl_samplerDv2_i(%opencl.image2d_ro_t*, %opencl.sampler_t*, double) #1

attributes #0 = { convergent noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="128" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { convergent nounwind readonly "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #2 = { convergent nounwind readonly }

!llvm.module.flags = !{!0}
!opencl.ocl.version = !{!1}
!llvm.ident = !{!2}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 2, i32 0}
!2 = !{!"clang version 10.0.0 (https://github.com/llvm/llvm-project.git 9cdcd81d3f2e9c1c9ae1e054e24668d46bc08bfb)"}
