//
// Created by xudong.chen on 25-6-3.
//

#include "device_8445_kst_limit.h"
#include "Xgimi_Debug.h"
#include <fstream>
#include <sstream>
#include <ctime>
#include <cstdio>

#undef TAG
#define TAG "GM_DISP_KST_8445_LIMIT"

#define WIDTH_4K (3840)
#define HEIGHT_4K (2160)

#define MULTI_POINT_LIMIT   (0.15)
#define SINGLE_POINT_LIMIT  (0.25)
#define BOND_LIMIT          (0.6)
#define ANGLE_LIMIT         (16)
#define SINGLE_WIDTH_LIMIT WIDTH_4K * SINGLE_POINT_LIMIT
#define SINGLE_HEIGHT_LIMIT HEIGHT_4K * SINGLE_POINT_LIMIT

const cv::Point TOP_LEFT = {0, 0};
const cv::Point TOP_RIGHT = {WIDTH_4K-1, 0};
const cv::Point BOTTOM_LEFT = {0, HEIGHT_4K-1};
const cv::Point BOTTOM_RIGHT = {WIDTH_4K-1, HEIGHT_4K-1};
#define FLOAT_GREATER(a, b) (std::abs((a)) > ((b) + 1e-6))
void Disp8445KstLimit::enableDebug(bool enable) {
    isDebugEnabled = enable;
    if(isDebugEnabled) {
        dbgHelper.createDebugPath();
        runKstTest();
    }
}

void Disp8445KstLimit::runKstTest() {
    // generate output path: /data/vendor/kst_test_result_{timestamp}.csv
    time_t now = std::time(nullptr);
    char outPath[128];
    std::snprintf(outPath, sizeof(outPath), "/data/vendor/kst_test_result_%ld.csv", (long)now);

    std::ofstream ofs(outPath);
    if (!ofs.is_open()) {
        XGIMI_DBG("%s[%d] Failed to open output file: %s\n", __FUNCTION__, __LINE__, outPath);
        return;
    }

    // write CSV header
    ofs << "Yaw,Pitch,TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y,OriginalErrorCode,isKstValid\n";

    int passCount = 0;
    int failCount = 0;
    for (int i = 0; i < KST_TEST_DATA_COUNT; ++i) {
        const KstTestEntry& e = KST_TEST_DATA[i];

        // update angle without side effects
        curKstAngle.yaw   = e.yaw;
        curKstAngle.pitch = e.pitch;

        // fill coordinates: [0][0]=TL, [0][1]=TR, [1][0]=BL, [1][1]=BR
        PointCoordinate point[2][2];
        point[0][0].S16X = e.tl_x;  point[0][0].S16Y = e.tl_y;
        point[0][1].S16X = e.tr_x;  point[0][1].S16Y = e.tr_y;
        point[1][0].S16X = e.bl_x;  point[1][0].S16Y = e.bl_y;
        point[1][1].S16X = e.br_x;  point[1][1].S16Y = e.br_y;

        bool result = isKstValid(point);
        if (result) ++passCount; else ++failCount;

        ofs << e.yaw << "," << e.pitch << ","
            << e.tl_x << "," << e.tl_y << ","
            << e.tr_x << "," << e.tr_y << ","
            << e.bl_x << "," << e.bl_y << ","
            << e.br_x << "," << e.br_y << ","
            << e.error_code << ","
            << (result ? "true" : "false") << "\n";
    }

    ofs.close();
    XGIMI_DBG("%s[%d] runKstTest done: total=%d pass=%d fail=%d output=%s\n",
        __FUNCTION__, __LINE__, KST_TEST_DATA_COUNT, passCount, failCount, outPath);
}

void Disp8445KstLimit::syncKstAngle(const KeystoneAngle_t& kstAngle) {
    XGIMI_DBG("%s[%d] kstAngle: pitch=%f, yaw=%f\n", __FUNCTION__, __LINE__,
        kstAngle.pitch, kstAngle.yaw);
    curKstAngle = kstAngle;
    XGIMI_DBG("%s[%d] kstAngle: pitch=%f, yaw=%f\n", __FUNCTION__, __LINE__,
        kstAngle.pitch, kstAngle.yaw);
}

bool Disp8445KstLimit::isKstValid(PointCoordinate point[2][2]) {
    if(FLOAT_GREATER(curKstAngle.pitch, ANGLE_LIMIT) || FLOAT_GREATER(curKstAngle.yaw, ANGLE_LIMIT)) {
        //如果侧投角度绝对值大于16度，使用软梯
        XGIMI_DBG("[%s:%d]Kst angle out of limit,use SWKeystone, pitch=%f, yaw=%f",__FUNCTION__,__LINE__, curKstAngle.pitch, curKstAngle.yaw);
        return false;
    }

    std::vector<cv::Point> quad = {
            {point[0][0].S16X, point[0][0].S16Y},
            {point[0][1].S16X, point[0][1].S16Y},
            {point[1][0].S16X, point[1][0].S16Y},
            {point[1][1].S16X, point[1][1].S16Y},
    };

    if(isFullScreen(quad)) {
        return true;
    }

    int chgIdx = findChangedPointIndex(quad);
    if(chgIdx != POINT_INVALID) {//发现只有一个点做了调整
        if(isDebugEnabled) {
            drawsingleAdjPicture(quad);
        }
        return singlePointLimit(quad, static_cast<PointIdx>(chgIdx));
    }

    std::vector<cv::Point> bond;
    computeBoundingBox(quad, bond);
    return PointLimitOfBond(quad, bond);

}

bool Disp8445KstLimit::isFullScreen(const std::vector<cv::Point>& points) {
    if (points[0].x == 0 && points[0].y == 0 &&
        points[1].x ==  WIDTH_4K - 1 && points[1].y == 0 &&
        points[2].x ==  0 && points[2].y == HEIGHT_4K - 1 &&
        points[3].x == WIDTH_4K - 1 && points[3].y == HEIGHT_4K - 1) {
        return true;
    }
    return false;
}

bool Disp8445KstLimit::singlePointLimit(const std::vector<cv::Point>& points, PointIdx id) {
    int limitWidth = SINGLE_WIDTH_LIMIT;
    int limitHeight = SINGLE_HEIGHT_LIMIT;

    auto point = points[id];

    if(id == POINT_LT) {
        limitWidth = SINGLE_WIDTH_LIMIT;
        limitHeight = SINGLE_HEIGHT_LIMIT;

        if(point.x >= 0 && point.y >= 0 &&
           point.x < limitWidth && point.y < limitHeight) {
            return true;
        }
    }else if(id == POINT_RT) {
        limitWidth = WIDTH_4K - SINGLE_WIDTH_LIMIT;
        limitHeight = SINGLE_HEIGHT_LIMIT;

        if(point.x < WIDTH_4K && point.y >= 0 &&
           point.x > limitWidth && point.y < limitHeight
        ){
            return true;
        }
    }else if(id == POINT_LB) {
        limitWidth = SINGLE_WIDTH_LIMIT;
        limitHeight = HEIGHT_4K - SINGLE_HEIGHT_LIMIT;

        if(point.x >= 0 && point.y < HEIGHT_4K &&
           point.x < limitWidth && point.y > limitHeight
        ){
            return true;
        }
    }else if(id == POINT_RB) {
        limitWidth = WIDTH_4K - SINGLE_WIDTH_LIMIT;
        limitHeight = HEIGHT_4K - SINGLE_HEIGHT_LIMIT;

        if(point.x < WIDTH_4K && point.y < HEIGHT_4K &&
           point.x > limitWidth && point.y > limitHeight
        ){
            return true;
        }
    }

    return false;
}

int Disp8445KstLimit::findChangedPointIndex(const std::vector<cv::Point>& points) {
    auto isVertex = [&](const cv::Point& point) {
        auto [x, y] = point;
        cv::Point TOP_LEFT = {0, 0};
        return
                (abs(x - TOP_LEFT.x) <= 0 && abs(y - TOP_LEFT.y) <= 0) ||
                (abs(x - TOP_RIGHT.x) <= 0 && abs(y - TOP_RIGHT.y) <= 0) ||
                (abs(x - BOTTOM_LEFT.x) <= 0 && abs(y - BOTTOM_LEFT.y) <= 0) ||
                (abs(x - BOTTOM_RIGHT.x) <= 0 && abs(y - BOTTOM_RIGHT.y) <= 0);
    };

    int vertexCount = 0;
    int changedIndex = -1;

    for (int i = 0; i < points.size(); ++i) {
        if (isVertex(points[i])) {
            vertexCount++;
        } else {
            if (changedIndex != -1) {
                return POINT_INVALID;
            }
            changedIndex = i;
        }
    }

    if (vertexCount == 3 && changedIndex != -1) {
        return changedIndex;
    }
    return POINT_INVALID;
}

bool Disp8445KstLimit::computeBoundingBox(const std::vector<cv::Point>& quad, std::vector<cv::Point>& bond) {
    // Initialize min/max values
    int minX = std::numeric_limits<int>::max();
    int maxX = std::numeric_limits<int>::min();
    int minY = std::numeric_limits<int>::max();
    int maxY = std::numeric_limits<int>::min();

    // Find min/max coordinates
    for (const auto& point : quad) {
        minX = std::min(minX, point.x);
        maxX = std::max(maxX, point.x);
        minY = std::min(minY, point.y);
        maxY = std::max(maxY, point.y);
    }

    // Set output coordinates
    bond.clear();
    bond.push_back({minX, minY});
    bond.push_back({maxX, minY});
    bond.push_back({minX, maxY});
    bond.push_back({maxX, maxY});

    return true;
}

bool Disp8445KstLimit::PointLimitOfBond(const std::vector<cv::Point>& points, const std::vector<cv::Point>& bond) {
    int bondWidth = bond[1].x - bond[0].x;
    int bondHeight = bond[2].y - bond[0].y;

    int limitWidth = (int)(bondWidth * MULTI_POINT_LIMIT);
    int limitHeight = (int)(bondHeight * MULTI_POINT_LIMIT);

    //debug
    if(isDebugEnabled) {
        drawBondPicture(points, bond, {limitWidth, limitHeight});
    }

    //bond need bigger than 60%
    if(bondWidth < (WIDTH_4K * BOND_LIMIT) || bondHeight < (HEIGHT_4K * BOND_LIMIT)) {
        XGIMI_DBG("%s[%d] bond too small, bondWidth:%d, bondHeight:%d\n", __FUNCTION__, __LINE__, bondWidth, bondHeight);
        return false;
    }

    cv::Point lt = points[0];
    cv::Point limitLt = {bond[0].x, bond[0].y};
    cv::Point limitRb = {bond[0].x + limitWidth, bond[0].y + limitHeight};
    if(lt.x < limitLt.x || lt.x > limitRb.x ||
       lt.y < limitLt.y || lt.y > limitRb.y
    ) {
        XGIMI_DBG("%s[%d] limit[{%d,%d},{%d,%d}],lt:{%d,%d}\n",__FUNCTION__,__LINE__,
               limitLt.x, limitLt.y, limitRb.x, limitRb.y, lt.x, lt.y);
        return false;
    }

    cv::Point rt = points[1];
    limitLt = {bond[1].x - limitWidth, bond[1].y};
    limitRb = {bond[1].x, bond[1].y + limitHeight};
    if(rt.x < limitLt.x || rt.x > limitRb.x ||
       rt.y < limitLt.y || rt.y > limitRb.y
    ){
        XGIMI_DBG("%s[%d] limit[{%d,%d},{%d,%d}],rt:{%d,%d}\n",__FUNCTION__,__LINE__,
               limitLt.x, limitLt.y, limitRb.x, limitRb.y, rt.x, rt.y);
        return false;
    }

    cv::Point lb = points[2];
    limitLt = {bond[2].x, bond[2].y - limitHeight};
    limitRb = {bond[2].x + limitWidth, bond[2].y};
    if(lb.x < limitLt.x || lb.x > limitRb.x ||
       lb.y < limitLt.y || lb.y > limitRb.y
     ){
        XGIMI_DBG("%s[%d] limit[{%d,%d},{%d,%d}],lb:{%d,%d}\n", __FUNCTION__,__LINE__,
               limitLt.x, limitLt.y, limitRb.x, limitRb.y, lb.x, lb.y);
        return false;
    }

    cv::Point rb = points[3];
    limitLt = {bond[3].x - limitWidth, bond[3].y - limitHeight};
    limitRb = {bond[3].x, bond[3].y};
    if(rb.x < limitLt.x || rb.x > limitRb.x ||
       rb.y < limitLt.y || rb.y > limitRb.y
    ) {
        XGIMI_DBG("%s[%d] limit[{%d,%d},{%d,%d}],rb:{%d,%d}\n", __FUNCTION__, __LINE__,
               limitLt.x, limitLt.y, limitRb.x, limitRb.y, rb.x, rb.y);
        return false;
    }
    return true;
}


//debug
void Disp8445KstLimit::drawsingleAdjPicture(const std::vector<cv::Point>& points) {
    std::vector<std::vector<cv::Point>> limits = {
            {//lt
                    {0, 0},
                    {static_cast<int>(SINGLE_WIDTH_LIMIT), 0},
                    {0, static_cast<int>(SINGLE_HEIGHT_LIMIT)},
                    {static_cast<int>(SINGLE_WIDTH_LIMIT), static_cast<int>(SINGLE_HEIGHT_LIMIT)}
            },
            {//rt
                    {static_cast<int>(WIDTH_4K - SINGLE_WIDTH_LIMIT), 0},
                    {WIDTH_4K, 0},
                    {static_cast<int>(WIDTH_4K - SINGLE_WIDTH_LIMIT), static_cast<int>(SINGLE_HEIGHT_LIMIT)},
                    {WIDTH_4K, static_cast<int>(SINGLE_HEIGHT_LIMIT)}
            },
            {//lb
                    {0, static_cast<int>(HEIGHT_4K - SINGLE_HEIGHT_LIMIT)},
                    {static_cast<int>(SINGLE_WIDTH_LIMIT), static_cast<int>(HEIGHT_4K - SINGLE_HEIGHT_LIMIT)},
                    {0, HEIGHT_4K},
                    {static_cast<int>(SINGLE_WIDTH_LIMIT), HEIGHT_4K}
            },
            {//rb
                    {static_cast<int>(WIDTH_4K - SINGLE_WIDTH_LIMIT), static_cast<int>(HEIGHT_4K - SINGLE_HEIGHT_LIMIT)},
                    {WIDTH_4K, static_cast<int>(HEIGHT_4K - SINGLE_HEIGHT_LIMIT)},
                    {static_cast<int>(WIDTH_4K - SINGLE_WIDTH_LIMIT), HEIGHT_4K},
                    {WIDTH_4K, HEIGHT_4K}
            }
    };
    dbgHelper.drawSinglePointKstAdjust(limits, points);
}

void Disp8445KstLimit::drawBondPicture(const std::vector<cv::Point>& points, const std::vector<cv::Point>& bond, std::pair<int, int> limitLen) {
    int limitWidth = limitLen.first;
    int limitHeight = limitLen.second;

    std::vector<std::vector<cv::Point>> limits = {
            {//lt
                    {bond[0].x, bond[0].y},
                    {bond[0].x + limitWidth, bond[0].y},
                    {bond[0].x, bond[0].y + limitHeight},
                    {bond[0].x + limitWidth, bond[0].y + limitHeight}
            },
            {//rt
                    {bond[1].x - limitWidth, bond[1].y},
                    {bond[1].x, bond[1].y},
                    {bond[1].x - limitWidth, bond[1].y + limitHeight},
                    {bond[1].x, bond[1].y + limitHeight}
            },
            {//lb
                    {bond[2].x, bond[2].y - limitHeight},
                    {bond[2].x + limitWidth, bond[2].y - limitHeight},
                    {bond[2].x, bond[2].y},
                    {bond[2].x + limitWidth, bond[2].y}
            },
            {//rb
                    {bond[3].x - limitWidth, bond[3].y - limitHeight},
                    {bond[3].x, bond[3].y - limitHeight},
                    {bond[3].x - limitWidth, bond[3].y},
                    {bond[3].x, bond[3].y}
            }
    };

    std::vector<cv::Point> full = {
        {
                {0, 0},
                {static_cast<int>(WIDTH_4K), 0},
                {0, static_cast<int>(HEIGHT_4K)},
                {static_cast<int>(WIDTH_4K), static_cast<int>(HEIGHT_4K)}
        },
    };

    dbgHelper.drawMultiPointKstAdjust(limits, bond, points, full);
}