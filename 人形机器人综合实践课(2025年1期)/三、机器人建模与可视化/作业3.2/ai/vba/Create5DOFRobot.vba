' ============================================================================
' Create5DOFRobot.vba - 纯直线代码，无子函数调用，与测试宏完全一致
' ============================================================================

Dim swApp As Object
Dim swModel As Object

Sub main()
    Set swApp = Application.SldWorks

    On Error Resume Next
    MkDir "D:\5DOF_Robot"
    MkDir "D:\5DOF_Robot\meshes"
    On Error GoTo 0

    Dim tp As String
    tp = swApp.GetUserPreferenceStringValue(8)  ' 零件模板

    Dim feat As Object
    Dim e As Long, w As Long

    ' ================================================================
    ' ============ 1. base_link: 圆柱 R=120mm H=80mm ================
    ' ================================================================
    Set swModel = swApp.NewDocument(tp, 0, 0#, 0#)
    swModel.Extension.SelectByID2 "上视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swModel.SketchManager.InsertSketch True
    swModel.SketchManager.CreateCircle 0#, 0#, 0#, 0.12, 0#, 0#
    swModel.SketchManager.InsertSketch True
    swModel.EditRebuild3
    swModel.Extension.SelectByID2 "草图1", "SKETCH", 0, 0, 0, False, 0, Nothing, 0
    Set feat = swModel.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, 0.08, 0.08, False, 0#, False, 0#, 0.01745329251994, 0.01745329251994, False, False, False, False, True, True, True, 0, 0#, False)
    swModel.EditRebuild3
    swModel.Extension.SaveAs "D:\5DOF_Robot\base_link.SLDPRT", 0, 1, Nothing, e, w
    swModel.Extension.SaveAs "D:\5DOF_Robot\meshes\base_link.stl", 0, 1, Nothing, e, w
    swApp.CloseDoc swModel.GetTitle

    ' ================================================================
    ' ============ 2. link_1: 圆柱 R=60mm H=60mm ====================
    ' ================================================================
    Set swModel = swApp.NewDocument(tp, 0, 0#, 0#)
    swModel.Extension.SelectByID2 "上视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swModel.SketchManager.InsertSketch True
    swModel.SketchManager.CreateCircle 0#, 0#, 0#, 0.06, 0#, 0#
    swModel.SketchManager.InsertSketch True
    swModel.EditRebuild3
    swModel.Extension.SelectByID2 "草图1", "SKETCH", 0, 0, 0, False, 0, Nothing, 0
    Set feat = swModel.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, 0.06, 0.06, False, 0#, False, 0#, 0.01745329251994, 0.01745329251994, False, False, False, False, True, True, True, 0, 0#, False)
    swModel.EditRebuild3
    swModel.Extension.SaveAs "D:\5DOF_Robot\link_1.SLDPRT", 0, 1, Nothing, e, w
    swModel.Extension.SaveAs "D:\5DOF_Robot\meshes\link_1.stl", 0, 1, Nothing, e, w
    swApp.CloseDoc swModel.GetTitle

    ' ================================================================
    ' ============ 3. link_2: 长方体 80x60x300mm =====================
    ' ================================================================
    Set swModel = swApp.NewDocument(tp, 0, 0#, 0#)
    swModel.Extension.SelectByID2 "上视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swModel.SketchManager.InsertSketch True
    swModel.SketchManager.CreateCenterRectangle 0#, 0#, 0#, 0.04, 0.03, 0#
    swModel.SketchManager.InsertSketch True
    swModel.EditRebuild3
    swModel.Extension.SelectByID2 "草图1", "SKETCH", 0, 0, 0, False, 0, Nothing, 0
    Set feat = swModel.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, 0.3, 0.3, False, 0#, False, 0#, 0.01745329251994, 0.01745329251994, False, False, False, False, True, True, True, 0, 0#, False)
    swModel.EditRebuild3
    swModel.Extension.SaveAs "D:\5DOF_Robot\link_2.SLDPRT", 0, 1, Nothing, e, w
    swModel.Extension.SaveAs "D:\5DOF_Robot\meshes\link_2.stl", 0, 1, Nothing, e, w
    swApp.CloseDoc swModel.GetTitle

    ' ================================================================
    ' ============ 4. link_3: 圆柱 R=35mm H=250mm ===================
    ' ================================================================
    Set swModel = swApp.NewDocument(tp, 0, 0#, 0#)
    swModel.Extension.SelectByID2 "上视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swModel.SketchManager.InsertSketch True
    swModel.SketchManager.CreateCircle 0#, 0#, 0#, 0.035, 0#, 0#
    swModel.SketchManager.InsertSketch True
    swModel.EditRebuild3
    swModel.Extension.SelectByID2 "草图1", "SKETCH", 0, 0, 0, False, 0, Nothing, 0
    Set feat = swModel.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, 0.25, 0.25, False, 0#, False, 0#, 0.01745329251994, 0.01745329251994, False, False, False, False, True, True, True, 0, 0#, False)
    swModel.EditRebuild3
    swModel.Extension.SaveAs "D:\5DOF_Robot\link_3.SLDPRT", 0, 1, Nothing, e, w
    swModel.Extension.SaveAs "D:\5DOF_Robot\meshes\link_3.stl", 0, 1, Nothing, e, w
    swApp.CloseDoc swModel.GetTitle

    ' ================================================================
    ' ============ 5. link_4: 圆柱 R=30mm H=120mm ===================
    ' ================================================================
    Set swModel = swApp.NewDocument(tp, 0, 0#, 0#)
    swModel.Extension.SelectByID2 "上视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swModel.SketchManager.InsertSketch True
    swModel.SketchManager.CreateCircle 0#, 0#, 0#, 0.03, 0#, 0#
    swModel.SketchManager.InsertSketch True
    swModel.EditRebuild3
    swModel.Extension.SelectByID2 "草图1", "SKETCH", 0, 0, 0, False, 0, Nothing, 0
    Set feat = swModel.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, 0.12, 0.12, False, 0#, False, 0#, 0.01745329251994, 0.01745329251994, False, False, False, False, True, True, True, 0, 0#, False)
    swModel.EditRebuild3
    swModel.Extension.SaveAs "D:\5DOF_Robot\link_4.SLDPRT", 0, 1, Nothing, e, w
    swModel.Extension.SaveAs "D:\5DOF_Robot\meshes\link_4.stl", 0, 1, Nothing, e, w
    swApp.CloseDoc swModel.GetTitle

    ' ================================================================
    ' ============ 6. link_5: 长方体 60x80x40mm ======================
    ' ================================================================
    Set swModel = swApp.NewDocument(tp, 0, 0#, 0#)
    swModel.Extension.SelectByID2 "上视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swModel.SketchManager.InsertSketch True
    swModel.SketchManager.CreateCenterRectangle 0#, 0#, 0#, 0.03, 0.04, 0#
    swModel.SketchManager.InsertSketch True
    swModel.EditRebuild3
    swModel.Extension.SelectByID2 "草图1", "SKETCH", 0, 0, 0, False, 0, Nothing, 0
    Set feat = swModel.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, 0.04, 0.04, False, 0#, False, 0#, 0.01745329251994, 0.01745329251994, False, False, False, False, True, True, True, 0, 0#, False)
    swModel.EditRebuild3
    swModel.Extension.SaveAs "D:\5DOF_Robot\link_5.SLDPRT", 0, 1, Nothing, e, w
    swModel.Extension.SaveAs "D:\5DOF_Robot\meshes\link_5.stl", 0, 1, Nothing, e, w
    swApp.CloseDoc swModel.GetTitle

    ' ================================================================
    ' ============ 7. 装配体 =========================================
    ' ================================================================
    Dim asmTp As String
    asmTp = swApp.GetUserPreferenceStringValue(9)

    Dim asmModel As Object
    Set asmModel = swApp.NewDocument(asmTp, 0, 0#, 0#)
    Dim asmTitle As String
    asmTitle = asmModel.GetTitle

    Dim partFiles As Variant
    Dim partHeights As Variant
    partFiles = Array("base_link", "link_1", "link_2", "link_3", "link_4", "link_5")
    partHeights = Array(0.08, 0.06, 0.3, 0.25, 0.12, 0.04)

    Dim curY As Double
    curY = 0#
    Dim i As Integer
    Dim oErr As Long, oWarn As Long

    For i = 0 To 5
        Dim pPath As String
        pPath = "D:\5DOF_Robot\" & partFiles(i) & ".SLDPRT"

        ' 先打开零件
        Dim pDoc As Object
        Set pDoc = swApp.OpenDoc6(pPath, 1, 0, "", oErr, oWarn)

        ' 切回装配体
        swApp.ActivateDoc2 asmTitle, False, oErr

        ' 插入
        Dim comp As Object
        Set comp = asmModel.AddComponent5(pPath, 0, "", False, "", 0#, curY, 0#)

        curY = curY + partHeights(i)
    Next i

    asmModel.EditRebuild3
    asmModel.ViewZoomtofit2
    asmModel.Extension.SaveAs "D:\5DOF_Robot\arm_5dof.SLDASM", 0, 1, Nothing, e, w

    MsgBox "完成! 请打开 D:\5DOF_Robot\arm_5dof.SLDASM 查看", vbInformation
End Sub
