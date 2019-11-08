; ModuleID = 'vadd_good.cl'
source_filename = "vadd_good.cl"
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: convergent nounwind uwtable
define dso_local spir_kernel void @vadd(float* nocapture readonly %a, float* nocapture readonly %b, float* nocapture %c, i32 %count, i32* nocapture readnone %ocludeHiddenCounter) local_unnamed_addr #0 !dbg !8 !kernel_arg_addr_space !24 !kernel_arg_access_qual !25 !kernel_arg_type !26 !kernel_arg_base_type !26 !kernel_arg_type_qual !27 {
entry:
  call void @llvm.dbg.value(metadata float* %a, metadata !18, metadata !DIExpression()), !dbg !28
  call void @llvm.dbg.value(metadata float* %b, metadata !19, metadata !DIExpression()), !dbg !28
  call void @llvm.dbg.value(metadata float* %c, metadata !20, metadata !DIExpression()), !dbg !28
  call void @llvm.dbg.value(metadata i32 %count, metadata !21, metadata !DIExpression()), !dbg !28
  call void @llvm.dbg.value(metadata i32* %ocludeHiddenCounter, metadata !22, metadata !DIExpression()), !dbg !28
  %call = tail call i64 @get_global_id(i32 0) #3, !dbg !29
  %conv = trunc i64 %call to i32, !dbg !29
  call void @llvm.dbg.value(metadata i32 %conv, metadata !23, metadata !DIExpression()), !dbg !28
  %cmp = icmp ult i32 %conv, %count, !dbg !30
  br i1 %cmp, label %if.then, label %if.end, !dbg !32

if.then:                                          ; preds = %entry
  %sext = shl i64 %call, 32, !dbg !33
  %idxprom = ashr exact i64 %sext, 32, !dbg !33
  %arrayidx = getelementptr inbounds float, float* %a, i64 %idxprom, !dbg !33
  %0 = load float, float* %arrayidx, align 4, !dbg !33, !tbaa !35
  %arrayidx3 = getelementptr inbounds float, float* %b, i64 %idxprom, !dbg !39
  %1 = load float, float* %arrayidx3, align 4, !dbg !39, !tbaa !35
  %add = fadd float %0, %1, !dbg !40
  %arrayidx5 = getelementptr inbounds float, float* %c, i64 %idxprom, !dbg !41
  store float %add, float* %arrayidx5, align 4, !dbg !42, !tbaa !35
  br label %if.end, !dbg !43

if.end:                                           ; preds = %if.then, %entry
  ret void, !dbg !44
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
!1 = !DIFile(filename: "vadd_good.cl", directory: "/home/sotiris/projects/oclude/utils")
!2 = !{}
!3 = !{i32 2, !"Dwarf Version", i32 4}
!4 = !{i32 2, !"Debug Info Version", i32 3}
!5 = !{i32 1, !"wchar_size", i32 4}
!6 = !{i32 1, i32 0}
!7 = !{!"clang version 10.0.0 (https://github.com/llvm/llvm-project.git 8455294f2ac13d587b13d728038a9bffa7185f2b)"}
!8 = distinct !DISubprogram(name: "vadd", scope: !1, file: !1, line: 1, type: !9, scopeLine: 3, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition | DISPFlagOptimized, unit: !0, retainedNodes: !17)
!9 = !DISubroutineType(cc: DW_CC_LLVM_OpenCLKernel, types: !10)
!10 = !{null, !11, !11, !11, !13, !15}
!11 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !12, size: 64)
!12 = !DIBasicType(name: "float", size: 32, encoding: DW_ATE_float)
!13 = !DIDerivedType(tag: DW_TAG_const_type, baseType: !14)
!14 = !DIBasicType(name: "unsigned int", size: 32, encoding: DW_ATE_unsigned)
!15 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !16, size: 64)
!16 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!17 = !{!18, !19, !20, !21, !22, !23}
!18 = !DILocalVariable(name: "a", arg: 1, scope: !8, file: !1, line: 1, type: !11)
!19 = !DILocalVariable(name: "b", arg: 2, scope: !8, file: !1, line: 1, type: !11)
!20 = !DILocalVariable(name: "c", arg: 3, scope: !8, file: !1, line: 1, type: !11)
!21 = !DILocalVariable(name: "count", arg: 4, scope: !8, file: !1, line: 2, type: !13)
!22 = !DILocalVariable(name: "ocludeHiddenCounter", arg: 5, scope: !8, file: !1, line: 2, type: !15)
!23 = !DILocalVariable(name: "i", scope: !8, file: !1, line: 4, type: !16)
!24 = !{i32 2, i32 2, i32 1, i32 0, i32 1}
!25 = !{!"none", !"none", !"none", !"none", !"none"}
!26 = !{!"float*", !"float*", !"float*", !"uint", !"int*"}
!27 = !{!"const", !"const", !"", !"", !""}
!28 = !DILocation(line: 0, scope: !8)
!29 = !DILocation(line: 4, column: 11, scope: !8)
!30 = !DILocation(line: 5, column: 9, scope: !31)
!31 = distinct !DILexicalBlock(scope: !8, file: !1, line: 5, column: 7)
!32 = !DILocation(line: 5, column: 7, scope: !8)
!33 = !DILocation(line: 7, column: 12, scope: !34)
!34 = distinct !DILexicalBlock(scope: !31, file: !1, line: 6, column: 3)
!35 = !{!36, !36, i64 0}
!36 = !{!"float", !37, i64 0}
!37 = !{!"omnipotent char", !38, i64 0}
!38 = !{!"Simple C/C++ TBAA"}
!39 = !DILocation(line: 7, column: 19, scope: !34)
!40 = !DILocation(line: 7, column: 17, scope: !34)
!41 = !DILocation(line: 7, column: 5, scope: !34)
!42 = !DILocation(line: 7, column: 10, scope: !34)
!43 = !DILocation(line: 8, column: 3, scope: !34)
!44 = !DILocation(line: 9, column: 1, scope: !8)
