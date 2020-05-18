; ModuleID = 'stress.cl'
source_filename = "stress.cl"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local spir_kernel void @iftest(i32* %buf) #0 !dbg !8 !kernel_arg_addr_space !13 !kernel_arg_access_qual !14 !kernel_arg_type !15 !kernel_arg_base_type !15 !kernel_arg_type_qual !16 {
entry:
  %buf.addr = alloca i32*, align 8
  %a = alloca i32, align 4
  %b = alloca i32, align 4
  %c = alloca i32, align 4
  %d = alloca i32, align 4
  %x = alloca i32, align 4
  store i32* %buf, i32** %buf.addr, align 8
  call void @llvm.dbg.declare(metadata i32** %buf.addr, metadata !17, metadata !DIExpression()), !dbg !18
  call void @llvm.dbg.declare(metadata i32* %a, metadata !19, metadata !DIExpression()), !dbg !20
  call void @llvm.dbg.declare(metadata i32* %b, metadata !21, metadata !DIExpression()), !dbg !22
  call void @llvm.dbg.declare(metadata i32* %c, metadata !23, metadata !DIExpression()), !dbg !24
  call void @llvm.dbg.declare(metadata i32* %d, metadata !25, metadata !DIExpression()), !dbg !26
  call void @llvm.dbg.declare(metadata i32* %x, metadata !27, metadata !DIExpression()), !dbg !28
  %0 = load i32, i32* %a, align 4, !dbg !29
  %tobool = icmp ne i32 %0, 0, !dbg !29
  br i1 %tobool, label %land.lhs.true, label %lor.lhs.false, !dbg !31

land.lhs.true:                                    ; preds = %entry
  %1 = load i32, i32* %b, align 4, !dbg !32
  %tobool1 = icmp ne i32 %1, 0, !dbg !32
  br i1 %tobool1, label %if.then, label %lor.lhs.false, !dbg !33

lor.lhs.false:                                    ; preds = %land.lhs.true, %entry
  %2 = load i32, i32* %c, align 4, !dbg !34
  %tobool2 = icmp ne i32 %2, 0, !dbg !34
  br i1 %tobool2, label %land.lhs.true3, label %if.end, !dbg !35

land.lhs.true3:                                   ; preds = %lor.lhs.false
  %3 = load i32, i32* %d, align 4, !dbg !36
  %tobool4 = icmp ne i32 %3, 0, !dbg !36
  br i1 %tobool4, label %if.then, label %if.end, !dbg !37

if.then:                                          ; preds = %land.lhs.true3, %land.lhs.true
  store i32 42, i32* %x, align 4, !dbg !38
  br label %if.end, !dbg !39

if.end:                                           ; preds = %if.then, %land.lhs.true3, %lor.lhs.false
  ret void, !dbg !40
}
; Function Attrs: nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local spir_kernel void @muchiftest(i32* %buf) #0 !dbg !41 !kernel_arg_addr_space !13 !kernel_arg_access_qual !14 !kernel_arg_type !15 !kernel_arg_base_type !15 !kernel_arg_type_qual !16 {
entry:
  %buf.addr = alloca i32*, align 8
  %a = alloca i32, align 4
  %b = alloca i32, align 4
  %c = alloca i32, align 4
  %d = alloca i32, align 4
  %e = alloca i32, align 4
  %f = alloca i32, align 4
  %x = alloca i32, align 4
  store i32* %buf, i32** %buf.addr, align 8
  call void @llvm.dbg.declare(metadata i32** %buf.addr, metadata !42, metadata !DIExpression()), !dbg !43
  call void @llvm.dbg.declare(metadata i32* %a, metadata !44, metadata !DIExpression()), !dbg !45
  call void @llvm.dbg.declare(metadata i32* %b, metadata !46, metadata !DIExpression()), !dbg !47
  call void @llvm.dbg.declare(metadata i32* %c, metadata !48, metadata !DIExpression()), !dbg !49
  call void @llvm.dbg.declare(metadata i32* %d, metadata !50, metadata !DIExpression()), !dbg !51
  call void @llvm.dbg.declare(metadata i32* %e, metadata !52, metadata !DIExpression()), !dbg !53
  call void @llvm.dbg.declare(metadata i32* %f, metadata !54, metadata !DIExpression()), !dbg !55
  call void @llvm.dbg.declare(metadata i32* %x, metadata !56, metadata !DIExpression()), !dbg !57
  %0 = load i32, i32* %a, align 4, !dbg !58
  %tobool = icmp ne i32 %0, 0, !dbg !58
  br i1 %tobool, label %land.lhs.true, label %lor.lhs.false, !dbg !60

land.lhs.true:                                    ; preds = %entry
  %1 = load i32, i32* %b, align 4, !dbg !61
  %tobool1 = icmp ne i32 %1, 0, !dbg !61
  br i1 %tobool1, label %if.then, label %lor.lhs.false, !dbg !62

lor.lhs.false:                                    ; preds = %land.lhs.true, %entry
  %2 = load i32, i32* %c, align 4, !dbg !63
  %tobool2 = icmp ne i32 %2, 0, !dbg !63
  br i1 %tobool2, label %if.then, label %if.else, !dbg !64

if.then:                                          ; preds = %lor.lhs.false, %land.lhs.true
  store i32 1, i32* %x, align 4, !dbg !65
  br label %if.end18, !dbg !66

if.else:                                          ; preds = %lor.lhs.false
  %3 = load i32, i32* %a, align 4, !dbg !67
  %tobool3 = icmp ne i32 %3, 0, !dbg !67
  br i1 %tobool3, label %if.then10, label %lor.lhs.false4, !dbg !69

lor.lhs.false4:                                   ; preds = %if.else
  %4 = load i32, i32* %b, align 4, !dbg !70
  %tobool5 = icmp ne i32 %4, 0, !dbg !70
  br i1 %tobool5, label %land.lhs.true6, label %if.else11, !dbg !71

land.lhs.true6:                                   ; preds = %lor.lhs.false4
  %5 = load i32, i32* %c, align 4, !dbg !72
  %tobool7 = icmp ne i32 %5, 0, !dbg !72
  br i1 %tobool7, label %land.lhs.true8, label %if.else11, !dbg !73

land.lhs.true8:                                   ; preds = %land.lhs.true6
  %6 = load i32, i32* %d, align 4, !dbg !74
  %tobool9 = icmp ne i32 %6, 0, !dbg !74
  br i1 %tobool9, label %if.then10, label %if.else11, !dbg !75

if.then10:                                        ; preds = %land.lhs.true8, %if.else
  store i32 2, i32* %x, align 4, !dbg !76
  br label %if.end17, !dbg !77

if.else11:                                        ; preds = %land.lhs.true8, %land.lhs.true6, %lor.lhs.false4
  %7 = load i32, i32* %e, align 4, !dbg !78
  %tobool12 = icmp ne i32 %7, 0, !dbg !78
  br i1 %tobool12, label %if.then15, label %lor.lhs.false13, !dbg !80

lor.lhs.false13:                                  ; preds = %if.else11
  %8 = load i32, i32* %a, align 4, !dbg !81
  %9 = load i32, i32* %b, align 4, !dbg !82
  %add = add nsw i32 %8, %9, !dbg !83
  %tobool14 = icmp ne i32 %add, 0, !dbg !83
  br i1 %tobool14, label %if.then15, label %if.else16, !dbg !84

if.then15:                                        ; preds = %lor.lhs.false13, %if.else11
  store i32 3, i32* %x, align 4, !dbg !85
  br label %if.end, !dbg !86

if.else16:                                        ; preds = %lor.lhs.false13
  store i32 4, i32* %x, align 4, !dbg !87
  br label %if.end

if.end:                                           ; preds = %if.else16, %if.then15
  br label %if.end17

if.end17:                                         ; preds = %if.end, %if.then10
  br label %if.end18

if.end18:                                         ; preds = %if.end17, %if.then
  %10 = load i32, i32* %a, align 4, !dbg !88
  %tobool19 = icmp ne i32 %10, 0, !dbg !88
  br i1 %tobool19, label %land.lhs.true20, label %if.end25, !dbg !90

land.lhs.true20:                                  ; preds = %if.end18
  %11 = load i32, i32* %b, align 4, !dbg !91
  %tobool21 = icmp ne i32 %11, 0, !dbg !91
  br i1 %tobool21, label %if.end25, label %land.lhs.true22, !dbg !92

land.lhs.true22:                                  ; preds = %land.lhs.true20
  %12 = load i32, i32* %d, align 4, !dbg !93
  %13 = load i32, i32* %f, align 4, !dbg !94
  %mul = mul nsw i32 %12, %13, !dbg !95
  %tobool23 = icmp ne i32 %mul, 0, !dbg !95
  br i1 %tobool23, label %if.then24, label %if.end25, !dbg !96

if.then24:                                        ; preds = %land.lhs.true22
  store i32 5, i32* %x, align 4, !dbg !97
  br label %if.end25, !dbg !98

if.end25:                                         ; preds = %if.then24, %land.lhs.true22, %land.lhs.true20, %if.end18
  ret void, !dbg !99
}
; Function Attrs: convergent noinline nounwind optnone uwtable
define dso_local spir_kernel void @whiletest(i32* %buf) #0 !dbg !100 !kernel_arg_addr_space !13 !kernel_arg_access_qual !14 !kernel_arg_type !15 !kernel_arg_base_type !15 !kernel_arg_type_qual !16 {
entry:
  %buf.addr = alloca i32*, align 8
  %a = alloca i32, align 4
  %b = alloca i32, align 4
  %c = alloca i32, align 4
  %d = alloca i32, align 4
  %x = alloca i32, align 4
  store i32* %buf, i32** %buf.addr, align 8
  call void @llvm.dbg.declare(metadata i32** %buf.addr, metadata !101, metadata !DIExpression()), !dbg !102
  call void @llvm.dbg.declare(metadata i32* %a, metadata !103, metadata !DIExpression()), !dbg !104
  call void @llvm.dbg.declare(metadata i32* %b, metadata !105, metadata !DIExpression()), !dbg !106
  call void @llvm.dbg.declare(metadata i32* %c, metadata !107, metadata !DIExpression()), !dbg !108
  call void @llvm.dbg.declare(metadata i32* %d, metadata !109, metadata !DIExpression()), !dbg !110
  call void @llvm.dbg.declare(metadata i32* %x, metadata !111, metadata !DIExpression()), !dbg !112
  store i32 1, i32* %c, align 4, !dbg !113
  store i32 1, i32* %b, align 4, !dbg !114
  store i32 1, i32* %a, align 4, !dbg !115
  store i32 -10, i32* %x, align 4, !dbg !116
  br label %while.cond, !dbg !117

while.cond:                                       ; preds = %while.body, %entry
  %0 = load i32, i32* %a, align 4, !dbg !118
  %tobool = icmp ne i32 %0, 0, !dbg !118
  br i1 %tobool, label %land.rhs, label %land.end, !dbg !119

land.rhs:                                         ; preds = %while.cond
  %1 = load i32, i32* %x, align 4, !dbg !120
  %tobool1 = icmp ne i32 %1, 0, !dbg !119
  br label %land.end

land.end:                                         ; preds = %land.rhs, %while.cond
  %2 = phi i1 [ false, %while.cond ], [ %tobool1, %land.rhs ], !dbg !121
  br i1 %2, label %while.body, label %while.end, !dbg !117

while.body:                                       ; preds = %land.end
  %3 = load i32, i32* %x, align 4, !dbg !122
  %inc = add nsw i32 %3, 1, !dbg !122
  store i32 %inc, i32* %x, align 4, !dbg !122
  br label %while.cond, !dbg !117, !llvm.loop !123

while.end:                                        ; preds = %land.end
  ret void, !dbg !124
}

attributes #0 = { convergent noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "denorms-are-zero"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "uniform-work-group-size"="false" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { nounwind readnone speculatable willreturn }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!3, !4, !5}
!opencl.ocl.version = !{!6}
!llvm.ident = !{!7}

!0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !1, producer: "clang version 10.0.0 (https://github.com/llvm/llvm-project.git 9cdcd81d3f2e9c1c9ae1e054e24668d46bc08bfb)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !2, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "stress.cl", directory: "/home/sotiris/projects/thesis_projects/oclude/tests/toy_kernels")
!2 = !{}
!3 = !{i32 7, !"Dwarf Version", i32 4}
!4 = !{i32 2, !"Debug Info Version", i32 3}
!5 = !{i32 1, !"wchar_size", i32 4}
!6 = !{i32 2, i32 0}
!7 = !{!"clang version 10.0.0 (https://github.com/llvm/llvm-project.git 9cdcd81d3f2e9c1c9ae1e054e24668d46bc08bfb)"}
!8 = distinct !DISubprogram(name: "iftest", scope: !1, file: !1, line: 1, type: !9, scopeLine: 1, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!9 = !DISubroutineType(cc: DW_CC_LLVM_OpenCLKernel, types: !10)
!10 = !{null, !11}
!11 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !12, size: 64)
!12 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!13 = !{i32 1}
!14 = !{!"none"}
!15 = !{!"int*"}
!16 = !{!""}
!17 = !DILocalVariable(name: "buf", arg: 1, scope: !8, file: !1, line: 1, type: !11)
!18 = !DILocation(line: 1, column: 36, scope: !8)
!19 = !DILocalVariable(name: "a", scope: !8, file: !1, line: 2, type: !12)
!20 = !DILocation(line: 2, column: 6, scope: !8)
!21 = !DILocalVariable(name: "b", scope: !8, file: !1, line: 2, type: !12)
!22 = !DILocation(line: 2, column: 9, scope: !8)
!23 = !DILocalVariable(name: "c", scope: !8, file: !1, line: 2, type: !12)
!24 = !DILocation(line: 2, column: 12, scope: !8)
!25 = !DILocalVariable(name: "d", scope: !8, file: !1, line: 2, type: !12)
!26 = !DILocation(line: 2, column: 15, scope: !8)
!27 = !DILocalVariable(name: "x", scope: !8, file: !1, line: 2, type: !12)
!28 = !DILocation(line: 2, column: 18, scope: !8)
!29 = !DILocation(line: 3, column: 6, scope: !30)
!30 = distinct !DILexicalBlock(scope: !8, file: !1, line: 3, column: 6)
!31 = !DILocation(line: 3, column: 8, scope: !30)
!32 = !DILocation(line: 3, column: 11, scope: !30)
!33 = !DILocation(line: 3, column: 13, scope: !30)
!34 = !DILocation(line: 3, column: 16, scope: !30)
!35 = !DILocation(line: 3, column: 18, scope: !30)
!36 = !DILocation(line: 3, column: 21, scope: !30)
!37 = !DILocation(line: 3, column: 6, scope: !8)
!38 = !DILocation(line: 3, column: 26, scope: !30)
!39 = !DILocation(line: 3, column: 24, scope: !30)
!40 = !DILocation(line: 4, column: 2, scope: !8)
!41 = distinct !DISubprogram(name: "muchiftest", scope: !1, file: !1, line: 7, type: !9, scopeLine: 7, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!42 = !DILocalVariable(name: "buf", arg: 1, scope: !41, file: !1, line: 7, type: !11)
!43 = !DILocation(line: 7, column: 40, scope: !41)
!44 = !DILocalVariable(name: "a", scope: !41, file: !1, line: 8, type: !12)
!45 = !DILocation(line: 8, column: 6, scope: !41)
!46 = !DILocalVariable(name: "b", scope: !41, file: !1, line: 8, type: !12)
!47 = !DILocation(line: 8, column: 9, scope: !41)
!48 = !DILocalVariable(name: "c", scope: !41, file: !1, line: 8, type: !12)
!49 = !DILocation(line: 8, column: 12, scope: !41)
!50 = !DILocalVariable(name: "d", scope: !41, file: !1, line: 8, type: !12)
!51 = !DILocation(line: 8, column: 15, scope: !41)
!52 = !DILocalVariable(name: "e", scope: !41, file: !1, line: 8, type: !12)
!53 = !DILocation(line: 8, column: 18, scope: !41)
!54 = !DILocalVariable(name: "f", scope: !41, file: !1, line: 8, type: !12)
!55 = !DILocation(line: 8, column: 21, scope: !41)
!56 = !DILocalVariable(name: "x", scope: !41, file: !1, line: 8, type: !12)
!57 = !DILocation(line: 8, column: 24, scope: !41)
!58 = !DILocation(line: 9, column: 6, scope: !59)
!59 = distinct !DILexicalBlock(scope: !41, file: !1, line: 9, column: 6)
!60 = !DILocation(line: 9, column: 8, scope: !59)
!61 = !DILocation(line: 9, column: 11, scope: !59)
!62 = !DILocation(line: 9, column: 13, scope: !59)
!63 = !DILocation(line: 9, column: 16, scope: !59)
!64 = !DILocation(line: 9, column: 6, scope: !41)
!65 = !DILocation(line: 9, column: 21, scope: !59)
!66 = !DILocation(line: 9, column: 19, scope: !59)
!67 = !DILocation(line: 10, column: 11, scope: !68)
!68 = distinct !DILexicalBlock(scope: !59, file: !1, line: 10, column: 11)
!69 = !DILocation(line: 10, column: 13, scope: !68)
!70 = !DILocation(line: 10, column: 16, scope: !68)
!71 = !DILocation(line: 10, column: 18, scope: !68)
!72 = !DILocation(line: 10, column: 21, scope: !68)
!73 = !DILocation(line: 10, column: 23, scope: !68)
!74 = !DILocation(line: 10, column: 26, scope: !68)
!75 = !DILocation(line: 10, column: 11, scope: !59)
!76 = !DILocation(line: 10, column: 31, scope: !68)
!77 = !DILocation(line: 10, column: 29, scope: !68)
!78 = !DILocation(line: 11, column: 11, scope: !79)
!79 = distinct !DILexicalBlock(scope: !68, file: !1, line: 11, column: 11)
!80 = !DILocation(line: 11, column: 13, scope: !79)
!81 = !DILocation(line: 11, column: 16, scope: !79)
!82 = !DILocation(line: 11, column: 20, scope: !79)
!83 = !DILocation(line: 11, column: 18, scope: !79)
!84 = !DILocation(line: 11, column: 11, scope: !68)
!85 = !DILocation(line: 11, column: 25, scope: !79)
!86 = !DILocation(line: 11, column: 23, scope: !79)
!87 = !DILocation(line: 12, column: 9, scope: !79)
!88 = !DILocation(line: 13, column: 6, scope: !89)
!89 = distinct !DILexicalBlock(scope: !41, file: !1, line: 13, column: 6)
!90 = !DILocation(line: 13, column: 8, scope: !89)
!91 = !DILocation(line: 13, column: 12, scope: !89)
!92 = !DILocation(line: 13, column: 14, scope: !89)
!93 = !DILocation(line: 13, column: 17, scope: !89)
!94 = !DILocation(line: 13, column: 21, scope: !89)
!95 = !DILocation(line: 13, column: 19, scope: !89)
!96 = !DILocation(line: 13, column: 6, scope: !41)
!97 = !DILocation(line: 13, column: 26, scope: !89)
!98 = !DILocation(line: 13, column: 24, scope: !89)
!99 = !DILocation(line: 14, column: 1, scope: !41)
!100 = distinct !DISubprogram(name: "whiletest", scope: !1, file: !1, line: 16, type: !9, scopeLine: 16, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!101 = !DILocalVariable(name: "buf", arg: 1, scope: !100, file: !1, line: 16, type: !11)
!102 = !DILocation(line: 16, column: 39, scope: !100)
!103 = !DILocalVariable(name: "a", scope: !100, file: !1, line: 17, type: !12)
!104 = !DILocation(line: 17, column: 6, scope: !100)
!105 = !DILocalVariable(name: "b", scope: !100, file: !1, line: 17, type: !12)
!106 = !DILocation(line: 17, column: 9, scope: !100)
!107 = !DILocalVariable(name: "c", scope: !100, file: !1, line: 17, type: !12)
!108 = !DILocation(line: 17, column: 12, scope: !100)
!109 = !DILocalVariable(name: "d", scope: !100, file: !1, line: 17, type: !12)
!110 = !DILocation(line: 17, column: 15, scope: !100)
!111 = !DILocalVariable(name: "x", scope: !100, file: !1, line: 17, type: !12)
!112 = !DILocation(line: 17, column: 18, scope: !100)
!113 = !DILocation(line: 18, column: 12, scope: !100)
!114 = !DILocation(line: 18, column: 8, scope: !100)
!115 = !DILocation(line: 18, column: 4, scope: !100)
!116 = !DILocation(line: 19, column: 4, scope: !100)
!117 = !DILocation(line: 22, column: 2, scope: !100)
!118 = !DILocation(line: 22, column: 9, scope: !100)
!119 = !DILocation(line: 22, column: 11, scope: !100)
!120 = !DILocation(line: 22, column: 14, scope: !100)
!121 = !DILocation(line: 0, scope: !100)
!122 = !DILocation(line: 22, column: 18, scope: !100)
!123 = distinct !{!123, !117, !122}
!124 = !DILocation(line: 31, column: 2, scope: !100)
