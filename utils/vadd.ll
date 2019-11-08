; ModuleID = 'vadd.cl'
source_filename = "vadd.cl"
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: convergent nounwind uwtable
define dso_local spir_kernel void @vadd(float* nocapture readonly %a, float* nocapture readonly %b, float* nocapture %c, i32 %count) local_unnamed_addr #0 !dbg !8 !kernel_arg_addr_space !22 !kernel_arg_access_qual !23 !kernel_arg_type !24 !kernel_arg_base_type !24 !kernel_arg_type_qual !25 {
entry:
  call void @llvm.dbg.value(metadata float* %a, metadata !16, metadata !DIExpression()), !dbg !26
  call void @llvm.dbg.value(metadata float* %b, metadata !17, metadata !DIExpression()), !dbg !26
  call void @llvm.dbg.value(metadata float* %c, metadata !18, metadata !DIExpression()), !dbg !26
  call void @llvm.dbg.value(metadata i32 %count, metadata !19, metadata !DIExpression()), !dbg !26
  %call = tail call i64 @get_global_id(i32 0) #3, !dbg !27
  %conv = trunc i64 %call to i32, !dbg !27
  call void @llvm.dbg.value(metadata i32 %conv, metadata !20, metadata !DIExpression()), !dbg !26
  %cmp = icmp ult i32 %conv, %count, !dbg !28
  br i1 %cmp, label %if.then, label %if.end, !dbg !30

if.then:                                          ; preds = %entry
  %sext = shl i64 %call, 32, !dbg !31
  %idxprom = ashr exact i64 %sext, 32, !dbg !31
  %arrayidx = getelementptr inbounds float, float* %a, i64 %idxprom, !dbg !31
  %0 = load float, float* %arrayidx, align 4, !dbg !31, !tbaa !32
  %arrayidx3 = getelementptr inbounds float, float* %b, i64 %idxprom, !dbg !36
  %1 = load float, float* %arrayidx3, align 4, !dbg !36, !tbaa !32
  %add = fadd float %0, %1, !dbg !37
  %arrayidx5 = getelementptr inbounds float, float* %c, i64 %idxprom, !dbg !38
  store float %add, float* %arrayidx5, align 4, !dbg !39, !tbaa !32
  br label %if.end, !dbg !38

if.end:                                           ; preds = %if.then, %entry
  ret void, !dbg !40
}

; Function Attrs: convergent
declare dso_local i64 @get_global_id(i32) local_unnamed_addr #1

; Function Attrs: nounwind readnone speculatable willreturn
declare void @llvm.dbg.value(metadata, metadata, metadata) #2

attributes #0 = { convergent nounwind uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="none" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "uniform-work-group-size"="true" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { convergent "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="none" "less-precise-fpmad"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #2 = { nounwind readnone speculatable willreturn }
attributes #3 = { convergent nounwind }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!3, !4, !5}
!opencl.ocl.version = !{!6}
!llvm.ident = !{!7}

!0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !1, producer: "clang version 10.0.0 (https://github.com/llvm/llvm-project.git 8455294f2ac13d587b13d728038a9bffa7185f2b)", isOptimized: true, runtimeVersion: 0, emissionKind: FullDebug, enums: !2, nameTableKind: None)
!1 = !DIFile(filename: "vadd.cl", directory: "/home/sotiris/projects/oclude/utils")
!2 = !{}
!3 = !{i32 2, !"Dwarf Version", i32 4}
!4 = !{i32 2, !"Debug Info Version", i32 3}
!5 = !{i32 1, !"wchar_size", i32 4}
!6 = !{i32 1, i32 0}
!7 = !{!"clang version 10.0.0 (https://github.com/llvm/llvm-project.git 8455294f2ac13d587b13d728038a9bffa7185f2b)"}
!8 = distinct !DISubprogram(name: "vadd", scope: !1, file: !1, line: 1, type: !9, scopeLine: 1, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition | DISPFlagOptimized, unit: !0, retainedNodes: !15)
!9 = !DISubroutineType(cc: DW_CC_LLVM_OpenCLKernel, types: !10)
!10 = !{null, !11, !11, !11, !13}
!11 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !12, size: 64)
!12 = !DIBasicType(name: "float", size: 32, encoding: DW_ATE_float)
!13 = !DIDerivedType(tag: DW_TAG_const_type, baseType: !14)
!14 = !DIBasicType(name: "unsigned int", size: 32, encoding: DW_ATE_unsigned)
!15 = !{!16, !17, !18, !19, !20}
!16 = !DILocalVariable(name: "a", arg: 1, scope: !8, file: !1, line: 1, type: !11)
!17 = !DILocalVariable(name: "b", arg: 2, scope: !8, file: !1, line: 1, type: !11)
!18 = !DILocalVariable(name: "c", arg: 3, scope: !8, file: !1, line: 1, type: !11)
!19 = !DILocalVariable(name: "count", arg: 4, scope: !8, file: !1, line: 1, type: !13)
!20 = !DILocalVariable(name: "i", scope: !8, file: !1, line: 2, type: !21)
!21 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!22 = !{i32 2, i32 2, i32 1, i32 0}
!23 = !{!"none", !"none", !"none", !"none"}
!24 = !{!"float*", !"float*", !"float*", !"uint"}
!25 = !{!"const", !"const", !"", !""}
!26 = !DILocation(line: 0, scope: !8)
!27 = !DILocation(line: 2, column: 10, scope: !8)
!28 = !DILocation(line: 3, column: 7, scope: !29)
!29 = distinct !DILexicalBlock(scope: !8, file: !1, line: 3, column: 5)
!30 = !DILocation(line: 3, column: 5, scope: !8)
!31 = !DILocation(line: 3, column: 23, scope: !29)
!32 = !{!33, !33, i64 0}
!33 = !{!"float", !34, i64 0}
!34 = !{!"omnipotent char", !35, i64 0}
!35 = !{!"Simple C/C++ TBAA"}
!36 = !DILocation(line: 3, column: 30, scope: !29)
!37 = !DILocation(line: 3, column: 28, scope: !29)
!38 = !DILocation(line: 3, column: 16, scope: !29)
!39 = !DILocation(line: 3, column: 21, scope: !29)
!40 = !DILocation(line: 4, column: 1, scope: !8)
