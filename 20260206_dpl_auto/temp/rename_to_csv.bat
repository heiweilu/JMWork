@echo off
echo 正在将.dat文件重命名为.csv...
echo.
ren "quadrant_1_left_top.dat" "quadrant_1_left_top.csv"
echo 已重命名: quadrant_1_left_top.dat -^> quadrant_1_left_top.csv
ren "quadrant_2_right_top.dat" "quadrant_2_right_top.csv"
echo 已重命名: quadrant_2_right_top.dat -^> quadrant_2_right_top.csv
ren "quadrant_3_left_bottom.dat" "quadrant_3_left_bottom.csv"
echo 已重命名: quadrant_3_left_bottom.dat -^> quadrant_3_left_bottom.csv
ren "quadrant_4_right_bottom.dat" "quadrant_4_right_bottom.csv"
echo 已重命名: quadrant_4_right_bottom.dat -^> quadrant_4_right_bottom.csv
echo.
echo 重命名完成！
pause
