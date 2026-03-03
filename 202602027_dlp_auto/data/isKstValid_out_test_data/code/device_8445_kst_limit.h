//
// Created by xudong.chen on 25-6-3.
//
#ifndef __DEVICE_8445_KST_LIMIT_H__
#define __DEVICE_8445_KST_LIMIT_H__

#include <opencv2/opencv.hpp>
#include "kst_debug.h"
#include "Device_DataType.h"
#include "kst_test_data.h"

class Disp8445KstLimit {
public:
    Disp8445KstLimit() = default;
    ~Disp8445KstLimit() = default;

    bool isKstValid(PointCoordinate point[2][2]);

    void enableDebug(bool enable);

    void syncKstAngle(const KeystoneAngle_t& kstAngle);

    void runKstTest();

private:
    typedef enum {
        POINT_INVALID = -1,
        POINT_LT = 0,
        POINT_RT = 1,
        POINT_LB = 2,
        POINT_RB = 3,
    }PointIdx;

    KstDbgHelper dbgHelper;
    KeystoneAngle_t curKstAngle;

    bool isFullScreen(const std::vector<cv::Point>& points);
    int findChangedPointIndex(const std::vector<cv::Point>& points);
    bool computeBoundingBox(const std::vector<cv::Point>& quad, std::vector<cv::Point>& bond);
    bool singlePointLimit(const std::vector<cv::Point>& points, PointIdx id);
    bool PointLimitOfBond(const std::vector<cv::Point>& points, const std::vector<cv::Point>& bond);
    //debug
    bool isDebugEnabled = false;
    void drawsingleAdjPicture(const std::vector<cv::Point>& points);
    void drawBondPicture(const std::vector<cv::Point>& points, const std::vector<cv::Point>& bond, std::pair<int, int> limitLen);
};


#endif //INC_8445KSTLIMIT_DEVICE_8445_KST_LIMIT_H
