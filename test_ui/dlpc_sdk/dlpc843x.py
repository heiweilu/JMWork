#-------------------------------------------------------------------------------
# Copyright (c) 2025 Texas Instruments Incorporated - http://www.ti.com/
#-------------------------------------------------------------------------------
#
# NOTE: This file is auto generated from a command definition file.
#       Please do not modify the file directly.                    
#
# Command Spec Version : 2.3.0+Beta_3.6bee241
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the
#   distribution.
#
#   Neither the name of Texas Instruments Incorporated nor the names of
#   its contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import struct
from enum import Enum

from .packer import *

class SysControllerConfigT(Enum):
    Single = 0
    DualPrimary = 2
    DualSecondary = 3
    QuadPrimary = 4
    QuadSecondary1 = 5
    QuadSecondary2 = 6
    QuadSecondary3 = 7

class CmdModeT(Enum):
    Bootrom = 0
    MainApplication = 1
    SecondaryBootApplication = 2

class CmdSystemTypeWriteT(Enum):
    FlashSystem = 2118808358

class CmdSystemTypeReadT(Enum):
    Unknown = 0
    FlashSystem = 1

class CmdExtVersionT(Enum):
    Production = 0
    Alpha = 10
    Beta = 11

class CmdFlashUpdateT(Enum):
    Lock = 0
    Unlock = 4154802215

class FlashSizeT(Enum):
    Size4Mbit = 0
    Size8Mbit = 1
    Size16Mbit = 2
    Size32Mbit = 3
    Size64Mbit = 4
    Size128Mbit = 5
    Size256Mbit = 6
    Size512Mbit = 7

class BootHoldReasonT(Enum):
    AppProgMode = 2
    SysInitFail = 4
    StayInBoot = 8
    FlInitFail = 16
    MemInitFail = 32

class CmdClearErrorHistorySignT(Enum):
    Clear = 3721182122

class CmdAccessWidthT(Enum):
    Uint32 = 0
    Uint16 = 1
    Uint08 = 2

class CmdSwitchTypeT(Enum):
    ToBootrom = 0
    ToMainApplicationViaReset = 1
    ToSecondaryBootApplication = 3

class ActChannelT(Enum):
    ActChannel1 = 0
    ActChannel2 = 1

class CmdPccAlgorithmT(Enum):
    Cca = 1
    Hsg = 2
    NoPcc = 0

class CwColorWheelNumsT(Enum):
    CwNum1St = 0
    CwNum2Nd = 1

class CwColorWheelSelectT(Enum):
    All = 2
    Cw1St = 0
    Cw2Nd = 1

class CwMultiWheelTrackingModeT(Enum):
    Fast = 2
    Normal = 1
    Slow = 0

class DataCommitMode(Enum):
    Command = 1
    Immediate = 0

class DataStoreMode(Enum):
    Eeprom = 0
    Flash = 1

class DdpFlashBlockT(Enum):
    ApplicationBinaryBlock = 4
    CalibrationDataBlock = 0
    ConfigDataBlock = 5
    OemDataBlock = 2
    SecondaryBootBlock = 3
    UserSettingsBlock = 1

class DdpSystemModeT(Enum):
    Debug = 3
    Fault = 1
    FwUpdate = 5
    Normal = 0
    PrepFwUpdate = 4
    Standby = 2

class DispCurtainColorT(Enum):
    Black = 0
    Blue = 3
    Cyan = 4
    Green = 2
    Magenta = 5
    Red = 1
    White = 7
    Yellow = 6

class DispExecuteCommandStateT(Enum):
    Failed = 5
    InProgress = 3
    InQueue = 2
    NotStarted = 0
    Pending = 1
    Successful = 4

class DispXprEnableModeT(Enum):
    Auto = 0
    Off = 2
    On = 1

class DlpAllColorIlluminationT(Enum):
    BlueColor = 2
    CyanColor = 3
    GreenColor = 1
    MagentaColor = 4
    RedColor = 0
    YellowColor = 5

class DmCalibBlocksT(Enum):
    CwLampData = 6
    SsiData = 0
    WpcCalibData = 1
    WpcCalibMatrixData = 2
    WarpMapData = 5
    XprData = 3
    XprWaveformData = 4

class DmDataT(Enum):
    Calibration = 1
    Scratchpad = 2
    Settings = 0

class DpDisplaySourceT(Enum):
    External = 0
    Splash = 2
    Tpg = 1

class DpStateCommandT(Enum):
    ConfigError = 0
    DetectingSource = 1
    SourceLocked = 2

class EbfColorChannelSelectT(Enum):
    Blue = 2
    Green = 0
    Red = 1

class ErrCodeT(Enum):
    BootRomCrcError = 13
    CaicConfig = 12202
    CaicDriver = 12203
    CaicFuncNotEnabled = 12206
    CaicIllumResNotRdy = 12207
    CaicInit = 12201
    CaicInvalid = 12400
    CaicInvalidParam = 12208
    CaicLut = 12204
    CaicNotSupported = 12205
    CfgBlockNotFound = 1621
    CfgIndexOor = 1620
    CfgLutNotFound = 1622
    CfgOverlayProtected = 1625
    CfgTableRevMismatch = 1618
    CfgTableSigMismatch = 1619
    CfgUnableToAllocateMemory = 1624
    CfgUnableToCreateMempool = 1623
    CmdbBytesDiscarded = 1601
    CmdbInvalidParameter = 1603
    CmdbInvalidReadSize = 1604
    CmdbReadUnderflow = 1602
    CmdhAllocatedBufferNotEnough = 1615
    CmdhBytesDiscarded = 1605
    CmdhCommandTableNotSorted = 1617
    CmdhInvalidBytesInRespPkt = 1614
    CmdhInvalidChecksum = 1613
    CmdhInvalidCmdByteSize = 1611
    CmdhInvalidCmdTable = 1609
    CmdhInvalidDestination = 1608
    CmdhInvalidHandle = 1610
    CmdhInvalidLength = 1612
    CmdhInvalidParameter = 1607
    CmdhPackOverflow = 1616
    CmdhUnpackUnderflow = 1606
    CmdFlashoutofrange = 14
    CmdFlashreadtimeout = 15
    CmdFlashsfcbusy = 16
    CmdFlashsfcstatustimeout = 17
    CmdFlashsfctxfifotimeout = 325
    CmdFlashstatustimeout = 18
    CmdFlashCommnFail = 5
    CmdFlashOpsLocked = 3
    CmdFlashRwNotInit = 6
    CmdInvalidaddress = 19
    CmdInvalidbytecount = 20
    CmdInvalidcommandformat = 22
    CmdInvalidcommandtype = 21
    CmdInvalidflashclockrate = 23
    CmdInvalidflashwritesequence = 24
    CmdInvalidmemwritelength = 25
    CmdInvalidopcode = 26
    CmdInvalidsignature = 27
    CmdInvalidParam = 1626
    CmdInvalidParameter = 7
    CmdIramCommnFail = 9
    CmdIramRwNotInit = 8
    CmdMismatchcommand = 28
    CmdMismatchcrcchksum = 29
    CmdMismatchpayloadsize = 30
    CmdNocommandavailable = 31
    CmdNovalidcommandfound = 32
    CmdSoftwarefifofull = 33
    CmdSystemBusy = 4
    CmdTxfifofull = 34
    CwaDelayOutOfRange = 3702
    DdpFlashAddrNumExceeded = 1903
    DdpFlashInitFailure = 1902
    DdpFlashInvalidBlockType = 1904
    DdpFlashTableNotPresent = 1901
    DdpFlashTableRevMismatch = 1905
    DdpInvalidFlagId = 40
    DdpInvalidFlashBlock = 1908
    DdpInvalidSplFlag = 1907
    DdpPbcIntCfg = 1906
    Disp3DEnabled = 3442
    Disp3DUnsupportedWithRollingBuffer = 3438
    DispCropDisplayResolutionMismatch = 3435
    DispCropFirstLinePlusCropLineBiggerThanImageHeight = 3412
    DispCropFirstPixelPlusCropWidthBiggerThanImageWidth = 3410
    DispCropHeightBiggerThanImageHeight = 3411
    DispCropHeightIsSmallerThanValidMinCropHeight = 3414
    DispCropWidthBiggerThanImageWidth = 3409
    DispCropWidthIsSmallerThanValidMinCropWidth = 3413
    DispDatapathUpdtEvtCreateFailed = 3428
    DispDatapathUpdtTaskCreateFailed = 3429
    DispDisableVsyncIrqFailed = 3420
    DispDisplayFirstLinePlusHieghtBiggerThanValidMaxHeight = 3406
    DispDisplayFirstPixelPlusWidthBiggerThanValidMaxWidth = 3404
    DispDisplayHeightBiggerThanValidMaxHeight = 3405
    DispDisplayHeightSmallerThanValidMinHeight = 3408
    DispDisplayResolutionMoreThanSupportedWithDoubleBuffer = 3440
    DispDisplayWidthBiggerThanValidMaxWidth = 3403
    DispDisplayWidthSmallerThanValidMinWidth = 3407
    DispDynImgUpdtEvtCreateFailed = 3426
    DispDynImgUpdtTaskCreateFailed = 3427
    DispEnableVsyncIrqFailed = 3419
    DispFsyncTimedOut = 3437
    DispInputImageHeightBiggerThanValidImageHeight = 3416
    DispInputImageHeightSmallerThanValidImageHeight = 3418
    DispInputImageWidthBiggerThanValidImageWidth = 3415
    DispInputImageWidthSmallerThanValidImageWidth = 3417
    DispInstallSwapCallbackFailed = 3423
    DispInstallVsyncHndlrFailed = 3421
    DispInvalidColor = 3431
    DispInvalidSource = 3402
    DispMaxPixelClock = 3434
    DispRbDbEvtCreateFailed = 3424
    DispRtaEvent = 3433
    DispSbEvtCreateFailed = 3425
    DispSourceDisplayResolutionMismatch = 3430
    DispSwapEvtCreateFailed = 3422
    DispUnsupportedXprMode = 3432
    DispUpdateInProgress = 3443
    DispVrrEnabled = 3441
    DispVrrUnsupportedWithDoubleBuffer = 3439
    DispXprModeIsNone = 3436
    DlpaCanNotWriteToRoRegister = 2203
    DlpaDeviceIndexOor = 2206
    DlpaFaultCondition = 2214
    DlpaFunctionNotSupported = 2212
    DlpaIlluminationDriveChannelOor = 2208
    DlpaIlluminationDriveLevelOor = 2207
    DlpaIlluminationFaultCondition = 2215
    DlpaIncorrectDeviceType = 2210
    DlpaInvalidDeviceId = 2209
    DlpaInvalidRegisterAccess = 2204
    DlpaNoDeviceConfigurationFound = 2201
    DlpaNumberOfConnectionsOor = 2211
    DlpaRegisterValueOor = 2205
    DlpaSspCsConflict = 2202
    DmdControllerInvalid = 3836
    DmdDmdClockSetupFail = 3835
    DmdDmdDeviceIdMismatch = 3838
    DmdDmdPoweredBeforeChangingTrueGlobal = 3834
    DmdFuseIdReadFailed = 3822
    DmdGlobalVbiasFail = 3825
    DmdHsifCommFail = 3827
    DmdHsifPwrDownFail = 3830
    DmdHsifPwrUpFail = 3826
    DmdInterfaceTrainingTimeout = 3840
    DmdInvalidForThisSystemConfiguration = 3823
    DmdInvalidPeridicTrainingMode = 3815
    DmdLsifCommFail = 3821
    DmdLsifDisableFail = 3831
    DmdLsifEnableFail = 3820
    DmdMirrorLockNotSupported = 3842
    DmdMirrorLockTimeout = 3841
    DmdMpcFail = 3837
    DmdNotParked = 3818
    DmdParkFail = 3829
    DmdPoweredBeforeChangingTrueGlobal = 3802
    DmdPowerAlreadyDisabled = 3839
    DmdPreconditionFail = 3843
    DmdRtcBusy = 3804
    DmdRtcHsTrainingErr1 = 3810
    DmdRtcHsTrainingErr2 = 3811
    DmdRtcHsTrainingErr3 = 3812
    DmdRtcHsTrainingErr4 = 3813
    DmdRtcHsTrainingErr5 = 3814
    DmdRtcHsTrainingError = 3809
    DmdRtcLsValidationErr1 = 3807
    DmdRtcLsValidationErr2 = 3808
    DmdRtcLsValidationError = 3806
    DmdRtcOperationNotCompleted = 3803
    DmdRtcWakeupError = 3805
    DmdSeqEnabled = 3819
    DmdTrainFalsePositive = 3801
    DmdTrainNarrowPassBand = 3817
    DmdTrainNoPassBand = 3816
    DmdTrueGlobalNotSupported = 3833
    DmdUnparkFail = 3828
    DmdVoltageDisableFail = 3832
    DmdVoltageEnableFail = 3824
    DmCalibBlockNotPresent = 13008
    DmDispUpdateInProgress = 13018
    DmEepromCommFailed = 13001
    DmEepromInitFailed = 13000
    DmEepromReadFailed = 13006
    DmEepromWriteFailed = 13005
    DmFlashEraseFailed = 13012
    DmFlashReadFailed = 13011
    DmFlashWriteFailed = 13013
    DmFlashWriteLimitReached = 13014
    DmI2CConfigConflict = 13015
    DmInvalidOffset = 13003
    DmInvalidRequest = 13009
    DmInvalidSize = 13016
    DmInUseDefaultMode = 13007
    DmManualWarpInvalidStorageIndex = 13020
    DmNotInImmediateMode = 13019
    DmNoScratchpadSchemaVersion = 13017
    DmSecondaryEepromCommFailed = 13010
    DmSecondaryEepromInitTimeout = 13002
    DmWriteDisabled = 13004
    DpDatapathNotReady = 10307
    DpDecoderPowerUp = 10303
    DpEnableBeforeInit = 10310
    DpEvtClearFailed = 10311
    DpEvtTimeout = 10304
    DpIncorrectSrcSettings = 10302
    DpInvalidSourceType = 10306
    DpMbxSend = 10301
    DpRouteDisplay = 10308
    DpRtaCreate = 10300
    DpSrcUnsupported = 10305
    DpUnableToStartSourceLock = 10309
    DtxFpdInvalidPort = 2802
    DtxInvalidLane = 2801
    DtxInvalidPolarity = 2804
    DtxInvalidSource = 2803
    Ebc3DlutTableSizeInvalid = 5502
    EbcMbxBusy = 5501
    EbfDriver = 5802
    EbfInit = 5801
    EbfInvalidFirstControlPointValue = 5806
    EbfInvalidGainIndex = 5808
    EbfInvalidGainValues = 5807
    EbfInvalidOffsetIndex = 5810
    EbfInvalidOffsetValues = 5809
    EbfInvalidParam = 5804
    EbfInvalidRegisterMode = 5811
    EbfLut = 5803
    EbfMinimumSpacing = 5805
    EepromDriverFailed = 12721
    EepromI2CApiCallFailed = 12724
    EepromI2CPortInvalid = 12720
    EepromInvalidAddr = 12722
    EepromInvalidDeviceType = 12725
    EepromInvalidReadSize = 12726
    ErrEepromSemAcquireFailedAcquireFailed = 12723
    ExecCcApi = 13303
    ExecCcFatal = 13301
    ExecCcGenericFail = 13300
    ExecCcKeying = 13304
    ExecCcRtoserr = 13302
    FlashInvaliddevice = 35
    FmtFdcTrainingMaskFail = 4501
    FrameInterruptConfigFail = 4602
    FrameRtosError = 4601
    FrameTaskCreateFail = 4603
    FtFlashtableIdError = 43
    FtFlashLocked = 44
    GeneralFailure = 0
    HdrNotEnabled = 4910
    HdrNotEnabledInSource = 4908
    HdrSystemBrigntnessNotSet = 4909
    HdrTypeOutOfRange = 4907
    I2CcmdConfigFail = 701
    I2CcmdListenFail = 703
    I2CcmdSlaveOpenFail = 702
    I2CArbitrationLost = 606
    I2CCallbackNotInstalled = 620
    I2CCmdLockError = 610
    I2CCmdToSlaveFail = 709
    I2CFnNotvalidInMode = 621
    I2CGrpEventFail = 612
    I2CGrpInvalidTimeout = 611
    I2CGrpUnexpectedEvent = 613
    I2CIntConfigFail = 708
    I2CIntDisableFail = 706
    I2CIntEnableFail = 707
    I2CInvalidFilterValue = 604
    I2CInvalidListenCmd = 622
    I2CInvalidMasterAddressMode = 602
    I2CInvalidPort = 614
    I2CInvalidPriority = 618
    I2CInvalidSclClockRate = 601
    I2CInvalidSlaveAddressMode = 603
    I2CInNonRtosMode = 705
    I2CListenaddressNotSet = 623
    I2CNotMaster = 625
    I2CNoAck = 605
    I2CNoSlaveTaskExist = 704
    I2CReadAbort = 615
    I2CReadTimeout = 608
    I2CSemCreateFail = 626
    I2CSemInUse = 624
    I2CSendStopTimeout = 609
    I2CSlaveBufferFull = 616
    I2CSlaveSuspended = 617
    I2CTaskcreateError = 619
    I2CWriteTimeout = 607
    ImgCfgNotFound = 4902
    ImgHdrGammaIndexOrr = 4914
    ImgHdrProcessingIsOn = 4912
    ImgHsgParamsOor = 4905
    ImgIncorrectGammaType = 4911
    ImgIncorrectSource = 4901
    ImgInputOor = 4904
    ImgInvalidArg = 4903
    ImgP7CcaDataInvalid = 4906
    ImgUserGammaIndexOrr = 4913
    InputParmErrorTypeIsInvalid = 41
    IqcAbortException = 10
    IqcPrefetchException = 11
    IqcUndefinedException = 12
    IqcUnknownException = 319
    Lcw3DKeystoneAnglesUnsupported = 3533
    LcwAnamorphicScalingNotSupported = 3534
    LcwAssertHorzBndr = 3605
    LcwAssertHorzCtrPt = 3608
    LcwAssertVertBndr = 3606
    LcwAssertVertCtrPt = 3609
    LcwBinarySeacrhError = 3655
    LcwCannotReadAnglesFromCorners = 3510
    LcwCannotReadOpticalParametersFromCorners = 3511
    LcwDisabled = 3507
    LcwDispInProgressPending = 3542
    LcwEmptyWarppoints = 3549
    LcwFsdelayCalculation = 3523
    LcwHcpExceedResolution = 3544
    LcwHcpInvalidSpacing = 3546
    LcwImageRotationNotSupported = 3506
    LcwInsuffBlanking = 3601
    LcwInvalidBlankingCalculation = 3645
    LcwInvalidFeatureSelection = 3505
    LcwInvalidHomography = 3648
    LcwInvalidHwpMinDist = 3643
    LcwInvalidIndexOfWp = 3530
    LcwInvalidKeystoneAngleParametersInput = 3512
    LcwInvalidMwEeprom = 3548
    LcwInvalidNumberOfHcp = 3527
    LcwInvalidNumberOfVcp = 3528
    LcwInvalidNumberOfWp = 3529
    LcwInvalidNVector = 3602
    LcwInvalidPhcpInvSpace = 3633
    LcwInvalidPhcpMinDist = 3631
    LcwInvalidPhcpMinSpace = 3632
    LcwInvalidPvcpInvSpace = 3639
    LcwInvalidPvcpMinDist = 3637
    LcwInvalidPvcpMinSpace = 3638
    LcwInvalidReferenceQuadrant = 3619
    LcwInvalidSamplingResHorz = 3646
    LcwInvalidSamplingResVert = 3647
    LcwInvalidShcpInvSpace = 3636
    LcwInvalidShcpMinDist = 3634
    LcwInvalidShcpMinSpace = 3635
    LcwInvalidSpacing = 3607
    LcwInvalidSpacingConfig = 3603
    LcwInvalidSvcpInvSpace = 3642
    LcwInvalidSvcpMinDist = 3640
    LcwInvalidSvcpMinSpace = 3641
    LcwInvalidUpdateMode = 3613
    LcwInvalidVwpMinDist = 3644
    LcwKeystoneAnglesGeometricFailure = 3515
    LcwKeystoneCornersCrossingDisplayResolution = 3521
    LcwKeystoneCornersGeometricFailure = 3516
    LcwKeystoneCornersNegativeInput = 3508
    LcwKeystoneCornersUnsupported = 3531
    LcwKeystoneCornerBottomEdgeInput = 3538
    LcwKeystoneCornerBottomLeftInput = 3519
    LcwKeystoneCornerBottomRightInput = 3520
    LcwKeystoneCornerLeftEdgeInput = 3537
    LcwKeystoneCornerRightEdgeInput = 3536
    LcwKeystoneCornerTopEdgeInput = 3535
    LcwKeystoneCornerTopLeftInput = 3517
    LcwKeystoneCornerTopRightInput = 3518
    LcwKeystoneOor = 3614
    LcwKeystoneTwoSameCorner = 3509
    LcwKeystoneUnsupportedInputOrOutputResolution = 3522
    LcwLessMapUnsupported = 3543
    LcwManualWarpInvalidMovement = 3541
    LcwManualWarpMissing = 3526
    LcwManualWarpUnsupported = 3532
    LcwMaxHres = 3502
    LcwMaxRowsorcol = 3610
    LcwMaxVres = 3504
    LcwMinHres = 3501
    LcwMinRowsorcol = 3611
    LcwMinVres = 3503
    LcwNonEmptyNVector = 3604
    LcwOutOfScopeThrowRatioInput = 3513
    LcwOutOfScopeVerticalOffsetInput = 3514
    LcwPkeyManualWarping = 3618
    LcwPkeyOnedTwod = 3617
    LcwSetSmoothwarpmap = 3612
    LcwSolveaxb = 3615
    LcwSolveaxblu8 = 3616
    LcwUpsCalculation = 3525
    LcwVarMapInvalidColIndex = 3540
    LcwVarMapInvalidColIndexInit = 3651
    LcwVarMapInvalidHorzDispl = 3652
    LcwVarMapInvalidRowIndex = 3539
    LcwVarMapInvalidRowIndexInit = 3650
    LcwVarMapInvalidVertDispl = 3653
    LcwVarMapPtSetAdjusted = 3654
    LcwVarMapUpsampleFail = 3649
    LcwVcpExceedResolution = 3545
    LcwVcpInvalidSpacing = 3547
    LcwVfifoAllocation = 3524
    Max = 32767
    MbmEvent = 10600
    MbmNomsg = 10603
    MbmNoresp = 10604
    MbmRecv = 10602
    MbmSend = 10601
    MemiAppInIramCrcError = 329
    MemiLoadAppCrcError = 328
    MsgCodeDdpInitEntry = 6004
    MsgCodeDdpInitExit = 6005
    MsgCodeFdmaGamEntry = 6008
    MsgCodeFdmaGamExit = 6009
    MsgCodeFdmaMemEntry = 6006
    MsgCodeFdmaMemExit = 6007
    MsgCodeFdmaSplashEntry = 6010
    MsgCodeFdmaSplashExit = 6011
    MsgCodeHeartBit = 6003
    MsgCodeMainEntry = 6000
    MsgCodeRtosEntry = 6001
    MsgCodeRtosTick = 6002
    MsgCodeSelfProfile1 = 7000
    MsgCodeSelfProfile2 = 7001
    MsgCodeSelfProfile3 = 7002
    MsgCodeSelfProfile4 = 7003
    _None = 1
    OtaAppBinSizeCorrupted = 13404
    OtaCurrentTaskNotCmdhTask = 13408
    OtaDisplayResNotNative = 13402
    OtaExecDispNotSuccessful = 13403
    OtaNotSupportedInFactoryModes = 13407
    OtaSeqNotAsyncMode = 13406
    OtaSrcTypeNot2D = 13405
    OtaSystemNotInFwUpdateMode = 13401
    PctlCmdhTaskNotIntialized = 10003
    PctlEventCreateFailed = 10001
    PctlNoCmdIxfAvailable = 10000
    PctlTaskCreateFailed = 10002
    PiccAutoCurrentEnabled = 12404
    PiccConfig = 12401
    PiccCurrentNotRdy = 12410
    PiccCurrentUpdate = 12411
    PiccDcInvalid = 12403
    PiccDcOutOfRange = 12402
    PiccDcRangeMode = 12407
    PiccDefaultCurr = 12408
    PiccDefaultDc = 12409
    PiccDiscreteDcMode = 12406
    PiccInvalid = 12600
    PiccSeqPending = 12412
    PiccWpcEnabled = 12405
    PkeyInitFailed = 8000
    PkeyLibVerNotCompatible = 8020
    PkeyPostValidateDeviceMismatch = 8003
    PkeyPreValidateDeviceMismatch = 8002
    PkeyPreValidateFailed = 8001
    PkeyProdFeatureUnsupported = 8005
    PkeyReadDmdFuseIdFailed = 8004
    RscAbfErr = 3712
    RscDrcRwcOutOfRange = 3717
    RscLec3DEnabledWithOverlap = 3705
    RscLec3DEnabledWithSingleBank = 3707
    RscLecInitNc = 3704
    RscLecLedTimeoutOor = 3703
    RscLecModeInvalid = 3711
    RscLecOverlapConfigTypeInvalid = 3709
    RscLecOverlapEnabledWith3D = 3706
    RscLecOverlapEnabledWithSingleBank = 3708
    RscLecStrobeTypeInvalid = 3710
    RscLecTestModeDisabled = 3716
    RscOutOfRange = 3701
    RscSeqInvalidSeqExecLutIndex = 3713
    RscSeqInvalidVectTableIndex = 3714
    RscSeqInvalidVectTableSize = 3715
    RscSeqTimeoutRange = 4008
    RtaFuncNotSupported = 13222
    RtaGenericFail = 13227
    RtaInvalidCaller = 13223
    RtaInvalidId = 13201
    RtaInvalidMsgDepth = 13215
    RtaInvalidMsgLength = 13226
    RtaInvalidMsgPriority = 13216
    RtaInvalidNumOpArgs = 13221
    RtaInvalidPtr = 13224
    RtaInvalidStackSize = 13219
    RtaInvalidTaskPriority = 13202
    RtaInvalidTicks = 13203
    RtaInvalidType = 13225
    RtaMbxFull = 13217
    RtaNotOwner = 13213
    RtaNoFreeEvent = 13210
    RtaNoFreeGrpevt = 13211
    RtaNoFreeMbx = 13214
    RtaNoFreeMempools = 13204
    RtaNoFreeMsg = 13218
    RtaNoFreeSem = 13212
    RtaNoFreeTask = 13206
    RtaNoStackMemPool = 13208
    RtaNsfMemory = 13205
    RtaNsfStackMemory = 13207
    RtaSemInUse = 13220
    RtaTimedOut = 13209
    RtpFdmaCrcerr = 317
    RtpFdmaEventclr = 307
    RtpFdmaEventset = 308
    RtpFdmaGrEvtCreate = 302
    RtpFdmaIntCfgCreate = 303
    RtpFdmaInvaldchannel = 305
    RtpFdmaInvalidbytecount = 326
    RtpFdmaInvalidDestAddrIncrMode = 312
    RtpFdmaInvalidSrcAddr = 310
    RtpFdmaInvalidSrcAddrmode = 311
    RtpFdmaInvalidUnpackMode = 313
    RtpFdmaSemrel = 309
    RtpFdmaSemres = 306
    RtpFdmaSemCreate = 301
    RtpFdmaStatusInvalid = 315
    RtpFdmaTimeout = 304
    RtpFdmaTransfersizeOor = 314
    RtpFdmaTransferFail = 316
    RtpGpioInvalidDualusePinAccess = 37
    RtpGpioInvalidPinAccess = 36
    RtpGptOor = 42
    RtpInvalidPeripheral = 2
    RtpIqcOor = 318
    RtpSfcParameterError = 327
    RtpSfcRxfifoOverrun = 320
    RtpSfcRxfifoUnderrun = 321
    RtpSfcTxfifoOverrun = 322
    RtpSfcTxfifoUnderrun = 323
    RtpSfcUndefinedError = 324
    Seq1BitColorTimeNotFound = 4013
    Seq1BitExecLutSwitch = 4014
    Seq1BitSqmSwitch = 4016
    SeqBpdIndexOutOfRange = 4006
    SeqBpdLutFull = 4007
    SeqBrightnessBinNotFound = 4023
    SeqColorTimeNotFound = 4004
    SeqCwSlowPhaseLockFeatureUnsupported = 4031
    SeqDiscreteDcNotSupported = 4021
    SeqDutycycleOutOfRange = 4024
    SeqEnableIsrFailed = 4010
    SeqFrameRateBinNotFound = 4020
    SeqIllumNotFound = 4003
    SeqIndexTableSizeExceeded = 4009
    SeqInputFrameRateNotValid = 4019
    SeqInvalidIndex = 4027
    SeqInvalidParam = 4028
    SeqInvalidSeDarkTimePercentage = 4022
    SeqLookIndexOutOfRange = 4001
    SeqMboxSizeBeyond32Kb = 4012
    SeqMultiBitExecLutSwitch = 4015
    SeqMultiBitSqmSwitch = 4017
    SeqNullPtr = 4026
    SeqOverlapNotSupported = 4025
    SeqRatefactorIndexExceeded = 4005
    SeqSeqColortimeNotSatisfied = 4011
    SeqSrcNotFound = 4002
    SeqStartTimeout = 4018
    SeqTaskIdNotAssigned = 4030
    SeqUnsupportedCommand = 4029
    SlcAlreadyInitalized = 2501
    SlcCfgSrc = 2508
    SlcEnableDisableSrc = 2507
    SlcIncorrectMsg = 2510
    SlcIncorrectState = 2506
    SlcNotInitialized = 2504
    SlcNullArgument = 2511
    SlcOperationTimeout = 2505
    SlcRtaCreate = 2502
    SlcUnableToSendMsg = 2509
    SpiioInvalidListenCmd = 1204
    SpiioInvalidSecondaryPort = 1202
    SpiioInvalidSecondaryPortChipsel = 1203
    SpiioNotEnabled = 1201
    SpiReadCallbackUninitialised = 1026
    SpiWriteCallbackUninitialised = 1027
    SplashBufferModeFetchFail = 5306
    SplashFrameRateOor = 5313
    SplashHeightOor = 5302
    SplashHfpOor = 5311
    SplashIndexNotSet = 5312
    SplashIndexOutOfBounds = 5308
    SplashInvalidHorizontalBackPorch = 5316
    SplashInvalidHorizontalFrontPorch = 5315
    SplashInvalidPixelFormat = 5304
    SplashInvalidVerticalFrontPorch = 5314
    SplashTransferFail = 5305
    SplashWidthOor = 5301
    SplashWrongInputSource = 5307
    SrcCfgNotFound = 2601
    SrcDsiCfgNotFound = 2615
    SrcDsiInvalidDatamap = 2617
    SrcDsiInvalidLane = 2616
    SrcDsiNotEnabled = 2650
    SrcEntryNotFound = 2603
    SrcFpdCannotEnableDisable = 2609
    SrcFpdCfgNotFound = 2610
    SrcFpdInvalidDatamap = 2612
    SrcFpdInvalidFrange = 2613
    SrcFpdInvalidMode = 2611
    SrcFpdNotEnabled = 2614
    SrcInvalidArg = 2607
    SrcInvalidClk = 2605
    SrcInvalidNumEntries = 2604
    SrcInvalidPolarityDetected = 2606
    SrcInvalidSource = 2602
    SrcUnableToUpdate = 2608
    SrcVboCfgNotFound = 2619
    SrcVboInvalidByteMode = 2621
    SrcVboInvalidDatamap = 2622
    SrcVboInvalidFrange = 2623
    SrcVboInvalidLanes = 2620
    SrcVboInvalidLaneConfig = 2624
    SrcVboNotEnabled = 2625
    SsfDmdHsDriveStrengthInvalidValue = 3112
    SsfDmdIfClkRateIsAboveSupportedRange = 3110
    SsfDmdIfClkRateIsBelowSupportedRange = 3109
    SsfDmdLsDriveStrengthInvalidValue = 3111
    SsfErrDcgPllLockFailure = 3108
    SsfInvalidArg = 3101
    SsfInvalidBootConfigType = 39
    SsfInvalidPeripheral = 38
    SsfMonNotEnabled = 3102
    SsfRequestedClockIsAboveAllowedMaxFreq = 3106
    SsfRequestedClockIsBelowAllowedMinFreq = 3105
    SsfRequestedClockIsOutOfAllowedFreq = 3107
    SsiCfgNotFound = 5401
    SsiCwBypassed = 5417
    SsiCwFwUpdateNotSupported = 5416
    SsiCwNotSpinning = 5415
    SsiInvalidChannel = 5402
    SsiInvalidDlpa = 5404
    SsiInvalidLimits = 5403
    SsiLedConTest = 5405
    SsiPwmCwPwmPortNotAvailable = 5412
    SsiPwmDisableValUndetermined = 5413
    SsiPwmInvalidCw = 5411
    SsiPwmInvalidDutyCycle = 5408
    SsiPwmInvalidFreq = 5407
    SsiPwmInvalidIncounter = 5410
    SsiPwmInvalidPort = 5406
    SsiPwmInvalidSmplRateOor = 5409
    SsiPwmMtrResetTimedOut = 5414
    SsiSnsDataNotReady = 12607
    SsiSnsInvalid = 12650
    SsiSnsInvalidChipId = 12603
    SsiSnsInvalidConfig = 12606
    SsiSnsInvalidI2CPort = 12605
    SsiSnsInvalidSensorType = 12601
    SsiSnsNotInitialized = 12602
    SsiSnsUnableToCommunicate = 12604
    SspDsNotPopulated = 1017
    SspGrpEventFail = 1014
    SspGrpInvalidTimeout = 1013
    SspIncorrectReadDataBytes = 1028
    SspInvalidAutoXferSize = 1016
    SspInvalidChipsel = 1006
    SspInvalidClockRate = 1008
    SspInvalidDataBits = 1007
    SspInvalidDuplex = 1004
    SspInvalidNumOfBytes = 1019
    SspInvalidPort = 1001
    SspInvalidPortMode = 1003
    SspInvalidProtocol = 1018
    SspInvalidSpiClockPhase = 1010
    SspInvalidSpiClockPolarity = 1009
    SspInvalidXferMode = 1005
    SspPortDisabled = 1002
    SspReceiveOverrunErr = 1012
    SspRtaInvalidCaller = 1030
    SspRtaInvalidTicks = 1029
    SspSemFail = 1024
    SspSemInvalidId = 1023
    SspSemInUse = 1021
    SspSemNotOwner = 1022
    SspSemTimedOut = 1020
    SspTimeout = 1011
    SspTransferFail = 1025
    SspUnexpectedError = 1015
    ThermistorNotAvailable = 12701
    TpgAomDataTransferFail = 5211
    TpgBorderWidthOor = 5202
    TpgInvalidColor = 5210
    TpgInvalidFrameRate = 5209
    TpgInvalidHblanking = 5207
    TpgInvalidHres = 5205
    TpgInvalidPattern = 5201
    TpgInvalidPatternParams = 5213
    TpgInvalidPixelClock = 5212
    TpgInvalidRampCfg = 5203
    TpgInvalidVblanking = 5208
    TpgInvalidVres = 5206
    TpgNotCurrentPattern = 5204
    TpgSourceNotSelected = 5214
    UmcBpdInvalidSize = 4304
    UmcEbdInvalid1DBpdSize = 4305
    UmcEbdInvalidBpdEntrySize = 4303
    UmcEbdInvalidBpdIndex = 4302
    UmcEbdInvalidBptIndex = 4301
    UnsupportedOperation = 32766
    UrtBreakErr = 812
    UrtCallbackNotInstalled = 823
    UrtFlowctrlNotValid = 821
    UrtFnNotvalidInMode = 819
    UrtFramingErr = 810
    UrtGrpEventFail = 816
    UrtGrpInvalidTimeout = 817
    UrtInvalidBaudRate = 802
    UrtInvalidDatabits = 804
    UrtInvalidFlowcontrol = 806
    UrtInvalidListenCmd = 824
    UrtInvalidParity = 803
    UrtInvalidPort = 801
    UrtInvalidRxDataPolarity = 818
    UrtInvalidRxDataSource = 822
    UrtInvalidRxTrigLevel = 807
    UrtInvalidStopbits = 805
    UrtInvalidTxTrigLevel = 808
    UrtOverrunErr = 813
    UrtParityErr = 811
    UrtPortDisabled = 809
    UrtPortInUse = 820
    UrtTimeout = 814
    UrtUnexpectedError = 815
    UsbInvalidEp = 1401
    UsbInvalidEpType = 1403
    UsbInvalidParam = 1404
    UsbInvalidPktSize = 1402
    UsbNotReady = 1407
    UsbNoFreeEps = 1406
    UsbTimeout = 1405
    Veml33291DataNotReady = 12654
    Veml33291IncorrectChipId = 12651
    Veml33291Invalid = 12700
    Veml33291InvalidI2CPort = 12653
    Veml33291InvalidSyncCount = 12655
    Veml33291UnableToCommunicate = 12652
    VgpDtxVboLaneModeCfgTimeout = 5317
    VgpInvalidArg = 2805
    VgpMbox0NotDisabled = 5310
    VgpMbox0SplashNotSelected = 5309
    VgpMbxBusy = 2806
    WpcCalc = 12009
    WpcCalib = 12001
    WpcConfig = 12000
    WpcDc = 12008
    WpcFuncDisabled = 12003
    WpcFuncEnabled = 12002
    WpcInvalid = 12200
    WpcLedInvalid = 12016
    WpcNotSupported = 12014
    WpcSnsInit = 12004
    WpcSnsOut = 12006
    WpcSnsVsyncConfig = 12005
    WpcSysCp = 12010
    WpcTargetDc = 12011
    WpcTargetGainNonZero = 12015
    WpcTimerInit = 12012
    WpcTwpNotSet = 12013

class HdrTransferFnT(Enum):
    Hlg = 1
    Pq = 0

class SeqSpokeTestModesT(Enum):
    AllSpksAllRevs = 3
    AllSpksOneRev = 2
    OneSpkAllRevs = 1
    OneSpkOneRev = 0

class SplashCompressionT(Enum):
    Rle20 = 1
    Uncompressed = 0

class SplashPixelFormatT(Enum):
    Rgb56516Bit = 0
    Rgb88824Bit = 3
    YcrCb42216Bit = 1

class Src3DFrameDominanceT(Enum):
    LeftFrameDominance = 0
    RightFrameDominance = 1

class SrcFpdDataMapT(Enum):
    SrcFpd16BppYcbCr422Mode0 = 13
    SrcFpd16BppYcbCr422Mode1 = 14
    SrcFpd20BppYcbCr422Mode0 = 10
    SrcFpd20BppYcbCr422Mode1 = 11
    SrcFpd20BppYcbCr422Mode2 = 12
    SrcFpd24BppRgbMode0 = 3
    SrcFpd24BppRgbMode1 = 4
    SrcFpd24BppYcbCr444Mode0 = 8
    SrcFpd24BppYcbCr444Mode1 = 9
    SrcFpd30BppRgbMode0 = 0
    SrcFpd30BppRgbMode1 = 1
    SrcFpd30BppRgbMode2 = 2
    SrcFpd30BppYcbCr444Mode0 = 5
    SrcFpd30BppYcbCr444Mode1 = 6
    SrcFpd30BppYcbCr444Mode2 = 7

class SrcFpdFRangeT(Enum):
    SrcFpdFrange10MhzTo40Mhz = 0
    SrcFpdFrange40MhzTo80Mhz = 1
    SrcFpdFrange80MhzTo160Mhz = 4

class SrcFpdInpLaneT(Enum):
    Ra = 0
    Rb = 1
    Rc = 2
    Rd = 3
    Re = 4

class SrcFpdOperationModeT(Enum):
    DualportEvenAOddB = 2
    DualportOddAEvenB = 3
    SingleportA = 0
    SingleportB = 1

class SrcVboByteModeT(Enum):
    SrcVbo3ByteMode = 0
    SrcVbo4ByteMode = 1
    SrcVbo5ByteMode = 2

class SrcVboDataMapT(Enum):
    SrcVbo16BppYcbCr422 = 9
    SrcVbo20BppYcbCr422 = 8
    SrcVbo24BppRgb = 4
    SrcVbo24BppYcbCr422 = 7
    SrcVbo24BppYcbCr444 = 5
    SrcVbo30BppRgb = 2
    SrcVbo30BppYcbCr444 = 3
    SrcVbo32BppYcbCr422 = 6
    SrcVbo36BppRgb = 0
    SrcVbo36BppYcbCr444 = 1

class SrcVboFRangeT(Enum):
    SrcVboFrange2GbpsTo600Mbps = 1
    SrcVboFrange4GbpsTo2Gbps = 0

class SrcVboNumLanesT(Enum):
    EightLane = 8
    FourLane = 4
    OneLane = 1
    TwoLane = 2

class SrcVboOutLaneT(Enum):
    Lane0 = 0
    Lane1 = 1
    Lane2 = 2
    Lane3 = 3
    Lane4 = 4
    Lane5 = 5
    Lane6 = 6
    Lane7 = 7

class Tmp411TempSensorT(Enum):
    LocalTempSensor = 0
    RemoteTempSensor = 1

class TpgColorT(Enum):
    Black = 0
    Blue = 4
    Cyan = 6
    Green = 2
    Magenta = 5
    Red = 1
    White = 7
    Yellow = 3

class WrpMwCpTypeT(Enum):
    EvenlySampledPointsByRowsAndColumns = 0
    UserDefinedAll32X18Points = 1

class Xpr4WayCommand(Enum):
    Actforcestop = 14
    Acttype = 3
    Clockwidth = 5
    Dacgain = 1
    Dacoffset = 6
    Fixeden = 0
    Fixedoutputval = 13
    Invpwma = 9
    Invpwmb = 10
    Outputsel = 4
    Ramplen = 7
    Segmentlen = 8
    Sfdelay = 2
    Sffilterval = 11
    Sfwatchdog = 12

class TpgForwardDiagColorT(Enum):
    Red = 1
    Green = 2
    Blue = 4

class TpgBackwardDiagColorT(Enum):
    Red = 1
    Green = 2
    Blue = 4

class TpgLegalDistT(Enum):
    TpgLegaldist3 = 3
    TpgLegaldist7 = 7
    TpgLegaldist15 = 15
    TpgLegaldist31 = 31
    TpgLegaldist63 = 63
    TpgLegaldist127 = 127
    TpgLegaldist255 = 255
    TpgLegaldist511 = 511
    TpgLegaldist1023 = 1023

class TpgHorzRampStepT(Enum):
    TpgHorzrampStep0P5 = 1
    TpgHorzrampStep1P0 = 2
    TpgHorzrampStep2P0 = 3
    TpgHorzrampStep0P25 = 5

class TpgVertRampStepT(Enum):
    TpgVertrampStep1P0 = 1
    TpgVertrampStep2P0 = 2
    TpgVertrampStep4P0 = 3

class TpgDoubleLineModeT(Enum):
    NormalOperation = 0
    DoubleLineMode = 1

class Summary:
    Command: str
    CommInterface: str
    Successful: bool

class ProtocolData:
    CommandDestination: int
    OpcodeLength: int
    BytesRead: int

class Data:
     ErrorCode: int                         # int
     CommandError: bool
     OperationalError: bool
     InitError: bool

class MemoryArray:
     StartAddress: int                      # int
     AddressIncrement: int                  # int
     AccessWidth: CmdAccessWidthT
     NumberOfWords: int                     # int
     NumberOfBytesPerWord: int              # int
     Data: bytearray

class HdrSourceConfiguration:
     Enable: bool
     TransferFunction: HdrTransferFnT
     MasterDisplayBlackLevel: float
     MasterDisplayWhiteLevel: float
     MasterDisplayColorGamutRedX: float
     MasterDisplayColorGamutRedY: float
     MasterDisplayColorGamutGreenX: float
     MasterDisplayColorGamutGreenY: float
     MasterDisplayColorGamutBlueX: float
     MasterDisplayColorGamutBlueY: float
     MasterDisplayColorGamutWhiteX: float
     MasterDisplayColorGamutWhiteY: float

class ImageCcaCoordinates:
     OriginalCoordinateRedX: float
     OriginalCoordinateRedY: float
     OriginalCoordinateRedLum: float
     OriginalCoordinateGreenX: float
     OriginalCoordinateGreenY: float
     OriginalCoordinateGreenLum: float
     OriginalCoordinateBlueX: float
     OriginalCoordinateBlueY: float
     OriginalCoordinateBlueLum: float
     OriginalCoordinateWhiteX: float
     OriginalCoordinateWhiteY: float
     OriginalCoordinateWhiteLum: float
     TargetCoordinateRedX: float
     TargetCoordinateRedY: float
     TargetCoordinateRedGain: float
     TargetCoordinateGreenX: float
     TargetCoordinateGreenY: float
     TargetCoordinateGreenGain: float
     TargetCoordinateBlueX: float
     TargetCoordinateBlueY: float
     TargetCoordinateBlueGain: float
     TargetCoordinateCyanX: float
     TargetCoordinateCyanY: float
     TargetCoordinateCyanGain: float
     TargetCoordinateMagentaX: float
     TargetCoordinateMagentaY: float
     TargetCoordinateMagentaGain: float
     TargetCoordinateYellowX: float
     TargetCoordinateYellowY: float
     TargetCoordinateYellowGain: float
     TargetCoordinateWhiteX: float
     TargetCoordinateWhiteY: float
     TargetCoordinateWhiteGain: float

class ImageHsg:
     HsgRedGain: float
     HsgRedSaturation: float
     HsgRedHue: float
     HsgGreenGain: float
     HsgGreenSaturation: float
     HsgGreenHue: float
     HsgBlueGain: float
     HsgBlueSaturation: float
     HsgBlueHue: float
     HsgCyanGain: float
     HsgCyanSaturation: float
     HsgCyanHue: float
     HsgMagentaGain: float
     HsgMagentaSaturation: float
     HsgMagentaHue: float
     HsgYellowGain: float
     HsgYellowSaturation: float
     HsgYellowHue: float
     HsgWhiteRedGain: float
     HsgWhiteGreenGain: float
     HsgWhiteBlueGain: float

class WpcLedCalibrationMatrix:
     CalibrationMatrix0: float
     CalibrationMatrix1: float
     CalibrationMatrix2: float
     CalibrationMatrix3: float
     CalibrationMatrix4: float
     CalibrationMatrix5: float
     CalibrationMatrix6: float
     CalibrationMatrix7: float
     CalibrationMatrix8: float

class WpcSensorCalibrationMatrix:
     CalibrationMatrix0: float
     CalibrationMatrix1: float
     CalibrationMatrix2: float
     CalibrationMatrix3: float
     CalibrationMatrix4: float
     CalibrationMatrix5: float
     CalibrationMatrix6: float
     CalibrationMatrix7: float
     CalibrationMatrix8: float

class LedCurrents:
     RedLevel: int                          # int
     GreenLevel: int                        # int
     BlueLevel: int                         # int
     YellowLevel: int                       # int
     CyanLevel: int                         # int
     MagentaLevel: int                      # int

class LedMaxCurrents:
     Red: int                               # int
     Green: int                             # int
     Blue: int                              # int
     Yellow: int                            # int
     Cyan: int                              # int
     Magenta: int                           # int

class LedMinCurrents:
     Red: int                               # int
     Green: int                             # int
     Blue: int                              # int
     Yellow: int                            # int
     Cyan: int                              # int
     Magenta: int                           # int

class DataInvalidate:
     InvalidateUserSettings: bool
     InvalidateSsiCalibrationData: bool
     InvalidateWpcCalibrationData: bool
     InvalidateWpcCalibrationMatrixData: bool
     InvalidateXprCalibrationData: bool
     InvalidateXprWaveformCalibrationData: bool
     InvalidateWarpMapData: bool
     InvalidateCwLampData: bool

class DataOperationsStatus:
     DataUpdateIsDisabled: bool
     UseFactoryDefault: bool
     ScratchpadAreaOffset: int              # int
     AvailableScartchpadArea: int           # int
     CommunicationWithEepromSuccessful: bool
     DataStorageMode: DataStoreMode
     UpdatedDataCommitPending: bool

class ColorDutyCycles:
     RedDutyCycle: float
     GreenDutyCycle: float
     BlueDutyCycle: float
     CyanDutyCycle: float
     MagentaDutyCycle: float
     YellowDutyCycle: float

class SourceTimingsAndErrors:
     PixelClockRate: int                    # int
     ActivePixelsPerLine: int               # int
     ActiveLinesPerFrame: int               # int
     FrameRate: int                         # int
     HSyncRate: int                         # int
     VerticalFrontPorch: int                # int
     VerticalBackPorch: int                 # int
     VerticalSyncWidth: int                 # int
     HorizontalFrontPorch: int              # int
     HorizontalBackPorch: int               # int
     HorizontalSyncWidth: int               # int
     TotalPixelsPerLine: int                # int
     TotalLinesPerFrame: int                # int
     InvalidAppl: bool
     InvalidAlpf: bool
     InvalidHorizontalBlanking: bool
     InvalidVerticalBlanking: bool
     InvalidHsyncWidth: bool
     InvalidVsyncWidth: bool
     InvalidClock: bool
     UnstableTppl: bool
     UnstableActiveArea: bool
     SystemMeasurementError: bool

class FpdSwizzlerMap:
     SrcFpdPortaLaneZa: SrcFpdInpLaneT
     SrcFpdPortaLaneZb: SrcFpdInpLaneT
     SrcFpdPortaLaneZc: SrcFpdInpLaneT
     SrcFpdPortaLaneZd: SrcFpdInpLaneT
     SrcFpdPortaLaneZe: SrcFpdInpLaneT
     SrcFpdPortbLaneZa: SrcFpdInpLaneT
     SrcFpdPortbLaneZb: SrcFpdInpLaneT
     SrcFpdPortbLaneZc: SrcFpdInpLaneT
     SrcFpdPortbLaneZd: SrcFpdInpLaneT
     SrcFpdPortbLaneZe: SrcFpdInpLaneT

class VboLaneConfiguration:
     TxLane0: SrcVboOutLaneT
     TxLane1: SrcVboOutLaneT
     TxLane2: SrcVboOutLaneT
     TxLane3: SrcVboOutLaneT
     TxLane4: SrcVboOutLaneT
     TxLane5: SrcVboOutLaneT
     TxLane6: SrcVboOutLaneT
     TxLane7: SrcVboOutLaneT

class DmdTrainingResults:
     IsChannelActive: bool
     IsPinActive: bool
     LastKnownGoodDll: bool
     BitResult6332: int                     # int
     BitResult3100: int                     # int
     HighPass: int                          # int
     LowPass: int                           # int
     DllDelay: int                          # int
     Error: ErrCodeT

class SystemErrors:
     DmdProjectMismatchError: bool
     DmdInitializationError: bool
     DmdLsifError: bool
     DmdHsifError: bool
     DmdTrainingError: bool
     DmdPowerDownError: bool
     DmdPreconditioningError: bool
     DmdParkError: bool
     ProductConfigurationFailed: bool
     DlpcInitializationError: bool
     SequencerError: bool
     SequenceSelectionFailed: bool
     TemperatureOvershoot: bool
     SequenceStalled: bool
     DisplayExecutionOnPowerupFailed: bool
     EepromInitializationError: bool
     DlpaCommError: bool
     LedFault: bool
     DutyCycleUpdateError: bool
     GpioConflictError: bool
     UartPort0CommError: bool
     SspPort0CommError: bool
     SspPort1CommError: bool
     I2CPort0CommError: bool
     I2CPort1CommError: bool
     UsbPortCommError: bool

class SystemStatus:
     SystemInitializationDone: bool
     SystemError: bool
     VideoPortError: bool
     DisplayResetAtPowerup: bool
     ActuatorCalibrationMode: bool
     SequencePhaselock: bool
     SequenceFrequencylock: bool
     RedLedEnabled: bool
     GreenLedEnabled: bool
     BlueLedEnabled: bool
     ColorWheelSpinning: bool
     ColorWheelPhaseLock: bool
     ColorWheelFrequencyLock: bool

class DlpaMainStatus:
     TsWarn: bool
     TsShut: bool
     BatLowWarn: bool
     BatLowShut: bool
     DmdFault: bool
     ProjOnInt: bool
     IllumFault: bool
     SupplyFault: bool

class KeystoneCornersQueued:
     TopLeftX: int                          # int
     TopLeftY: int                          # int
     TopRightX: int                         # int
     TopRightY: int                         # int
     BottomLeftX: int                       # int
     BottomLeftY: int                       # int
     BottomRightX: int                      # int
     BottomRightY: int                      # int

class TpgGrid:
     LineColor: TpgColorT
     BackgroundColor: TpgColorT
     HorzWidth: int                         # int
     VertWidth: int                         # int
     HorzDistBetweenLines: int              # int
     VertDistBetweenLines: int              # int

_readcommand = None
_writecommand = None

def DLPC843Xinit(readcommandcb, writecommandcb):
    global _readcommand
    global _writecommand
    _readcommand = readcommandcb
    _writecommand = writecommandcb

    global Summary
    Summary.CommInterface = "DLPC843X"

    global PortocolData
    ProtocolData.CommandDestination = 0
    ProtocolData.OpcodeLength = 0
    ProtocolData.BytesRead = 0

def ReadMode():
    "This command returns whether the controller software is in Boot ROM or in the main application."
    global Summary
    Summary.Command = "Read Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    ActiveApplicationObj = 0
    ControllerConfigurationObj = 0
    try:
        writebytes=list(struct.pack('B',0))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        ActiveApplicationObj = getbits(3, 0);
        ControllerConfigurationObj = getbits(3, 3);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, CmdModeT(ActiveApplicationObj), SysControllerConfigT(ControllerConfigurationObj)

def WriteSwitchApplication(SwitchTo):
    "This command is used to switch between BootROM to Application and vice versa. When a hard reset to the Boot Application is issued and pin TSTPT_0 is held high, the controller will transfer to BootROM. TSTPT_0 will only be sampled for 1us after reset or power on. If TSTPT_0 is low when the command is issued, the controller will transfer to the secondary boot. <br>WARNING: If command is issued for jumping to Boot Application from Main Application, then returning back to Main Application is not possible without re-programming the Main Application."
    global Summary
    Summary.Command = "Write Switch Application"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',2))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',SwitchTo.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadVersion():
    "This command returns the version of the currently active application. The currently active application can be queried using the Get Mode command."
    global Summary
    Summary.Command = "Read Version"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',1))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(3, writebytes, ProtocolData)
        Major = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        Minor = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        Patch = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Major, Minor, Patch

def ReadExtendedSoftwareVersion():
    "This command returns the Pre-Release Info and Commit ID of software version residing in the Controller."
    global Summary
    Summary.Command = "Read Extended Software Version"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',4))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(10, writebytes, ProtocolData)
        PreReleaseNameObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        PreReleaseVersion = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        TestBuildNumber = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        CommitId = str(bytearray(readbytes), encoding)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, CmdExtVersionT(PreReleaseNameObj), PreReleaseVersion, TestBuildNumber, CommitId

def ReadBootHoldReason():
    "This command returns the code that specifies the reason for being in bootloader mode."
    global Summary
    Summary.Command = "Read Boot Hold Reason"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',18))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        ReasonObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, BootHoldReasonT(ReasonObj)

def WriteSystemType(SystemType,  EnableDebugMessages):
    "This command can be used to enter the desired system type. System type can only be selected once. Subsequent calls to this function are ignored and cannot be switched without a system restart."
    global Summary
    Summary.Command = "Write System Type"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',3))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',SystemType.value)))
        writebytes.extend(list(struct.pack('B',EnableDebugMessages)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadSystemType():
    "This command returns the system type."
    global Summary
    Summary.Command = "Read System Type"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',3))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        SystemTypeObj = getbits(3, 0);
        EnableDebugMessages = getbits(1, 3);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, CmdSystemTypeReadT(SystemTypeObj), EnableDebugMessages

def WriteClearErrorHistory(Signature):
    "This command clears all entries in the error history. The 32-bit parameter is a signature to prevent accidental calls."
    global Summary
    Summary.Command = "Write Clear Error History"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',5))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',Signature.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadErrorHistory():
    "This command reads the error history."
    global Summary
    Summary.Command = "Read Error History"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',6))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(249, writebytes, ProtocolData)
        NumberOfErrors = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        Data = readbytes[1:]  # Invalid ArrayType placeholder fixed
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, NumberOfErrors, Data

def ReadFlashId():
    "This command returns the flash device and manufacturer IDs."
    global Summary
    Summary.Command = "Read Flash Id"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',32))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        ManufacturerId = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        DeviceId = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        CapacityId = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ManufacturerId, DeviceId, CapacityId

def ReadGetFlashSectorInformation():
    "This command returns the flash sector information read from CFI compliant flash device."
    global Summary
    Summary.Command = "Read Get Flash Sector Information"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',33))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(7, writebytes, ProtocolData)
        FlashSizeObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        SectorSize = struct.unpack_from ('I', bytearray(readbytes), 1)[0]
        NumSectors = struct.unpack_from ('H', bytearray(readbytes), 5)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, FlashSizeT(FlashSizeObj), SectorSize, NumSectors

def WriteUnlockFlashForUpdate(Unlock):
    "This command unlocks the flash update operation (Download, Erase). By default the flash update operations are locked. This is to prevent accidental modification of flash contents. To unlock the pre-defined key shall be send as the unlock code. Calling this command with any other parameter will lock the flash update commands."
    global Summary
    Summary.Command = "Write Unlock Flash For Update"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',34))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',Unlock.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadUnlockFlashForUpdate():
    "This command returns whether the flash is in unlocked state."
    global Summary
    Summary.Command = "Read Unlock Flash For Update"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',34))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        IsUnlocked = struct.unpack_from ('?', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, IsUnlocked

def WriteEraseSector(SectorAddress):
    "This command erases the sector of the flash of the given address. This command is a flash update command and requires flash operations to be unlocked using Unlock Flash for Update command. The sector address shall be specified as an offset from flash start address. For example, in a flash device where all sectors are 64KB of size, sector addresses shall be specified as follows: <br> Sector 0 = 0 <br> Sector 1 = 0x10000 <br> Sector 2 = 0x20000 <br> ... <br>"
    global Summary
    Summary.Command = "Write Erase Sector"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',35))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',SectorAddress)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteFullFlashErase():
    "This command does a full chip erase. This command is a flash update command and requires flash operations to be unlocked using the Unlock Flash for Update command."
    global Summary
    Summary.Command = "Write Full Flash Erase"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',40))
        ProtocolData.OpcodeLength = 1;
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteInitializeFlashReadWriteSettings(StartAddress,  NumBytes):
    "This command initializes flash read/write operation. This command shall be called before Flash Write or Flash Read command is sent. Note: For Flash Write/Read, the Start Address and Num Bytes set up shall both be multiple of 4."
    global Summary
    Summary.Command = "Write Initialize Flash Read Write Settings"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',36))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',StartAddress)))
        writebytes.extend(list(struct.pack('I',NumBytes)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteFlashWrite(Data):
    "This command is used to program data to flash. The write command is only available in boot application. This command shall be called only after setting the start address and size using the Initialize Flash Read Write Settings command. This command is a flash update command and requires flash operations to be unlocked using Unlock Flash for Update command. Flash Write commands can be chained until the initialized number of bytes are programmed. The BootROM will auto-increment the address and size for each command. Only the initialized number of bytes will be programmed even if more data is provided. It is important to send only multiple of 4 number of bytes per flash write command to ensure all bytes are written. This is done so that all flash writes are optimized as per the multi-word write supported by the flash device. For SPI communication, SSP buffer size is 64 bytes. The Host needs to send 65 bytes (64 bytes data + 1 dummy byte - needed for mode 0 operation). This command supports variable sized payload. Number of bytes to write is always expected to be a multiple of 4 bytes. The command fails if the number of bytes requested to write is not a multiple of 4 bytes."
    global Summary
    Summary.Command = "Write Flash Write"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',37))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(Data))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadFlashWrite(NumBytesToRead):
    "This command is used to read data from flash. This command shall be called only after setting the start address and size using the Initialize Flash Read Write command. Flash Read commands can be chained until the initialized number of bytes are returned. The BootROM will auto-increment the address and size for each command. Only the initialized number of bytes will be returned. Calling the function after returning requested data will result in command failure. This command supports variable sized response. Number of bytes to write is always expected to be a multiple of 4 bytes. Command returns error if it is not multiple of 4."
    global Summary
    Summary.Command = "Read Flash Write"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',37))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',NumBytesToRead)))
        readbytes = _readcommand(0, writebytes, ProtocolData)
        Data = bytearray(readbytes)[0, 1]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Data

def ReadChecksum(StartAddress,  NumBytes):
    "This command computes and returns the checksum starting at the given address for the specified number of bytes. Checksum is calculated as below:- <BR> uint32 SimpleChecksum = 0; <BR> uint32 SumofSumChecksum = 0; <BR> uint08 *Addr = (uint08 *) StartAddress; <BR> <BR> while (NumBytes--) <BR> { <BR> SimpleChecksum += *Addr++; <BR> SumofSumChecksum += SimpleChecksum; <BR> } <BR>"
    global Summary
    Summary.Command = "Read Checksum"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',38))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',StartAddress)))
        writebytes.extend(list(struct.pack('I',NumBytes)))
        readbytes = _readcommand(8, writebytes, ProtocolData)
        SimpleChecksum = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
        SumOfSumChecksum = struct.unpack_from ('I', bytearray(readbytes), 4)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, SimpleChecksum, SumOfSumChecksum

def WriteMemory(Address,  Value):
    "This command attempts a direct write of the given 32-bit value to the given 32-bit memory address. The memory address is not verified whether it is valid to write to the location."
    global Summary
    Summary.Command = "Write Memory"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',16))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',Address)))
        writebytes.extend(list(struct.pack('I',Value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadMemory(Address):
    "This command returns the 32-bit value stored at the given 32-bit memory address."
    global Summary
    Summary.Command = "Read Memory"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',16))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',Address)))
        readbytes = _readcommand(4, writebytes, ProtocolData)
        Value = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Value

def WriteMemoryArray(MemoryArray):
    "Writes a stream of words into the RAM memory starting from the address specified. Performs no checks as to whether the specified memory address given is valid or not."
    global Summary
    Summary.Command = "Write Memory Array"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',17))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',MemoryArray.StartAddress)))
        packerinit()
        value = setbits(int(MemoryArray.AddressIncrement), 6, 0)
        value = setbits(MemoryArray.AccessWidth.value, 2, 6)
        writebytes.extend(list(struct.pack('B',value)))
        writebytes.extend(list(struct.pack('H',MemoryArray.NumberOfWords)))
        writebytes.extend(list(struct.pack('B',MemoryArray.NumberOfBytesPerWord)))
        writebytes.extend(list(MemoryArray.Data))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadMemoryArray(StartAddress,  AddressIncrement,  AccessWidth,  NumberOfWords,  NumberOfBytesPerWord):
    "Reads a stream of words from memory starting from the address specified. Performs no checks as to whether the specified memory address given is valid or not."
    global Summary
    Summary.Command = "Read Memory Array"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',17))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',StartAddress)))
        packerinit()
        value = setbits(int(AddressIncrement), 6, 0)
        value = setbits(AccessWidth.value, 2, 6)
        writebytes.extend(list(struct.pack('B',value)))
        writebytes.extend(list(struct.pack('H',NumberOfWords)))
        writebytes.extend(list(struct.pack('B',NumberOfBytesPerWord)))
        readbytes = _readcommand(0, writebytes, ProtocolData)
        Data = bytearray(readbytes)[0, 1]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Data

def WriteBlendingFunctionControl(Enable):
    "This command disables or enables EBF processing. <br>"
    global Summary
    Summary.Command = "Write Blending Function Control"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',88))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadBlendingFunctionControl():
    "This command returns the EBF processing enable state. <br>"
    global Summary
    Summary.Command = "Read Blending Function Control"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',88))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable

def WriteBlendmapControlPoints(HorizontalCtrlPoints,  VerticalCtrlPoints):
    "This command takes input of the user defined control points location in horizontal and vertical direction as part of the Blend Map <br>"
    global Summary
    Summary.Command = "Write Blendmap Control Points"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',89))
        ProtocolData.OpcodeLength = 1;
        pass  # Invalid ArrayType placeholder fixed
        pass  # Invalid ArrayType placeholder fixed
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadBlendmapControlPoints():
    "This command gets the user defined blend map control points location stored in EEPROM. <br>"
    global Summary
    Summary.Command = "Read Blendmap Control Points"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',89))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(128, writebytes, ProtocolData)
        pass  # Invalid ArrayType placeholder fixed
        pass  # Invalid ArrayType placeholder fixed
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, HorizontalCtrlPoints, VerticalCtrlPoints

def WriteBlendmapGainValues(ColorChannelSelect,  BlendMapGainIndex,  GainValues):
    "This command takes input from the user of Gain values of control points as part of the Blend Map <br>"
    global Summary
    Summary.Command = "Write Blendmap Gain Values"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',90))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',ColorChannelSelect.value)))
        writebytes.extend(list(struct.pack('H',BlendMapGainIndex)))
        pass  # Invalid ArrayType placeholder fixed
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadBlendmapGainValues(ColorChannelSelect,  BlendMapGainIndex,  NumEntries):
    "This command reads from the blend map table already loaded using CMD_WriteBlendMapGainValues command. N Blend map gain values (that does not exceed the command packet size) can be read at a time from anywhere within the table. <br>"
    global Summary
    Summary.Command = "Read Blendmap Gain Values"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',90))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',ColorChannelSelect.value)))
        writebytes.extend(list(struct.pack('H',BlendMapGainIndex)))
        writebytes.extend(list(struct.pack('H',NumEntries)))
        readbytes = _readcommand(0, writebytes, ProtocolData)
        pass  # Invalid ArrayType placeholder fixed
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, GainValues

def WriteBlendmapOffsetValues(ColorChannelSelect,  BlendMapOffsetIndex,  OffsetValues):
    "This command takes input from the user of Offset values of control points as part of the Blend Map <br>"
    global Summary
    Summary.Command = "Write Blendmap Offset Values"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',91))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',ColorChannelSelect.value)))
        writebytes.extend(list(struct.pack('H',BlendMapOffsetIndex)))
        pass  # Invalid ArrayType placeholder fixed
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadBlendmapOffsetValues(ColorChannelSelect,  BlendMapOffsetIndex,  NumEntries):
    "This command reads from the blend map table already loaded using CMD_WriteBlendMapOffsetValues command. N Blend map Offset values (that does not exceed the command packet size) can be read at a time from anywhere within the table. <br>"
    global Summary
    Summary.Command = "Read Blendmap Offset Values"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',91))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',ColorChannelSelect.value)))
        writebytes.extend(list(struct.pack('H',BlendMapOffsetIndex)))
        writebytes.extend(list(struct.pack('H',NumEntries)))
        readbytes = _readcommand(0, writebytes, ProtocolData)
        pass  # Invalid ArrayType placeholder fixed
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, OffsetValues

def WriteHdrSourceConfiguration(HdrSourceConfiguration):
    "HDR maps wider brightness and color range of HDR sources to projector brightness and color range. The mapping requires multiple source groups and system groups to define the HDR source and projection device properties respectively. This command sets the source properties and based on this information nearest source group is selected for mapping. <br>"
    global Summary
    Summary.Command = "Write Hdr Source Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',113))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(HdrSourceConfiguration.Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        writebytes.extend(list(struct.pack('B',HdrSourceConfiguration.TransferFunction.value)))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayBlackLevel,65536)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayWhiteLevel,65536)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayColorGamutRedX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayColorGamutRedY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayColorGamutGreenX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayColorGamutGreenY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayColorGamutBlueX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayColorGamutBlueY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayColorGamutWhiteX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(HdrSourceConfiguration.MasterDisplayColorGamutWhiteY,32768)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadHdrSourceConfiguration():
    "This command returns the metadata information. <br>"
    global Summary
    Summary.Command = "Read Hdr Source Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',113))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(26, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        HdrSourceConfiguration.Enable = getbits(1, 0);
        HdrSourceConfiguration.TransferFunction = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        HdrSourceConfiguration.MasterDisplayBlackLevel = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 2)[0], 65536)
        HdrSourceConfiguration.MasterDisplayWhiteLevel = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 6)[0], 65536)
        HdrSourceConfiguration.MasterDisplayColorGamutRedX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 10)[0], 32768)
        HdrSourceConfiguration.MasterDisplayColorGamutRedY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 12)[0], 32768)
        HdrSourceConfiguration.MasterDisplayColorGamutGreenX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 14)[0], 32768)
        HdrSourceConfiguration.MasterDisplayColorGamutGreenY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 16)[0], 32768)
        HdrSourceConfiguration.MasterDisplayColorGamutBlueX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 18)[0], 32768)
        HdrSourceConfiguration.MasterDisplayColorGamutBlueY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 20)[0], 32768)
        HdrSourceConfiguration.MasterDisplayColorGamutWhiteX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 22)[0], 32768)
        HdrSourceConfiguration.MasterDisplayColorGamutWhiteY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 24)[0], 32768)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, HdrSourceConfiguration

def WriteSystemBrightnessRangeSetting(MinimumBrightness,  MaximumBrightness):
    "This command sets the system brightness range in nits. These are used in determining the appropriate transfer functions to be applied on the HDR source. This only needs to be set for HDR functionality. <br>"
    global Summary
    Summary.Command = "Write System Brightness Range Setting"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',115))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(MinimumBrightness,65536)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(MaximumBrightness,65536)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadSystemBrightnessRangeSetting():
    "This command returns currently set HDR system brightness range. <br>"
    global Summary
    Summary.Command = "Read System Brightness Range Setting"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',115))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(8, writebytes, ProtocolData)
        MinimumBrightness = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 0)[0], 65536)
        MaximumBrightness = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 4)[0], 65536)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, MinimumBrightness, MaximumBrightness

def WriteWpcEnable(WpcEnable):
    "This command enables the WPC function. <br>White Point Correction (WPC) is a function that automatically adjusts the duty cycles for the red, green, and blue LEDs until the target white point is achieved. The target white point for each Look is set in the firmware. Use command Get Look to read the target white point for the active Look.    <br> When enabled, WPC runs continuously. The controller regularly reads measured data from the light sensor and makes updates to the duty cycles. Continuous operation assures that any drift in the white point over time such as due to LED heating is removed and the target white point is always maintained.    <br> For proper convergence and operation of the WPC algorithm, WPC Sensor Calibration Data must be loaded via Set WPC Calibration Data command or via EEPROM before enabling WPC.<br> <br>Note that the Dynamic Black commands will take precedence over other color processing algorithms. <br>"
    global Summary
    Summary.Command = "Write Wpc Enable"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',116))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(WpcEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadWpcEnable():
    "This command returns whether WPC is enable or disabled. <br>"
    global Summary
    Summary.Command = "Read Wpc Enable"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',116))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        WpcEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, WpcEnable

def ReadWpcDutyCycles():
    "This command reads the LED duty cycles after adjustments by the WPC algorithm have been made.    <br> <br>When WPC is enabled via command Set WPC Enable, WPC automatically adjusts the LED duty cycles until the target white point is achieved. A light sensor embedded in the system is used to monitor the illumination light applied to the DMD.  <br> Before reading duty cycles with this command, make sure WPC is enabled.  <br> The target white point, and the target duty cycles that nominally achieve this white point, can be read with command Get Look. To maintain the target white point the actual LED duty cycles used by WPC will vary from the target values as needed to compensate for system opto-mechanical tolerances and LED performance drift with temperature and aging. <br>"
    global Summary
    Summary.Command = "Read Wpc Duty Cycles"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',118))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(6, writebytes, ProtocolData)
        Red = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 0)[0], 256)
        Green = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 2)[0], 256)
        Blue = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 4)[0], 256)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Red, Green, Blue

def ReadWpcSensorOutput():
    "This command reads the measured output data from the integrating light sensor for red, green, and blue light.<br> Values returned are those read by the controller directly from registers in the light sensor device. For byte data formats see the applicable sensor device data sheet. <br>"
    global Summary
    Summary.Command = "Read Wpc Sensor Output"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',119))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(12, writebytes, ProtocolData)
        Red = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
        Green = struct.unpack_from ('I', bytearray(readbytes), 4)[0]
        Blue = struct.unpack_from ('I', bytearray(readbytes), 8)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Red, Green, Blue

def WriteImageCcaCoordinates(ImageCcaCoordinates):
    "This command allows independent adjustment of the primary, secondary and white coordinates. This call will override any CCA settings performed by prior calls. <br>Note : CCA is not recommended with Color overlap systems due to performace issues, HSG is recommended for color overlap systems. <br>"
    global Summary
    Summary.Command = "Write Image Cca Coordinates"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',120))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateRedX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateRedY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateRedLum,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateGreenX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateGreenY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateGreenLum,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateBlueX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateBlueY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateBlueLum,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateWhiteX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateWhiteY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.OriginalCoordinateWhiteLum,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateRedX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateRedY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateRedGain,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateGreenX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateGreenY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateGreenGain,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateBlueX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateBlueY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateBlueGain,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateCyanX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateCyanY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateCyanGain,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateMagentaX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateMagentaY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateMagentaGain,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateYellowX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateYellowY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateYellowGain,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateWhiteX,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateWhiteY,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageCcaCoordinates.TargetCoordinateWhiteGain,32768)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImageCcaCoordinates():
    "This command returns the current color coordinate configuration. <br>"
    global Summary
    Summary.Command = "Read Image Cca Coordinates"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',120))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(66, writebytes, ProtocolData)
        ImageCcaCoordinates.OriginalCoordinateRedX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 0)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateRedY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 2)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateRedLum = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 4)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateGreenX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 6)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateGreenY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 8)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateGreenLum = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 10)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateBlueX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 12)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateBlueY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 14)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateBlueLum = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 16)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateWhiteX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 18)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateWhiteY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 20)[0], 32768)
        ImageCcaCoordinates.OriginalCoordinateWhiteLum = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 22)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateRedX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 24)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateRedY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 26)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateRedGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 28)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateGreenX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 30)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateGreenY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 32)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateGreenGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 34)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateBlueX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 36)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateBlueY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 38)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateBlueGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 40)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateCyanX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 42)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateCyanY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 44)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateCyanGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 46)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateMagentaX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 48)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateMagentaY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 50)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateMagentaGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 52)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateYellowX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 54)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateYellowY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 56)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateYellowGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 58)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateWhiteX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 60)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateWhiteY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 62)[0], 32768)
        ImageCcaCoordinates.TargetCoordinateWhiteGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 64)[0], 32768)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ImageCcaCoordinates

def WriteImageHsg(ImageHsg):
    "This command applies the given hue, saturation and gain values for all colors. It does not affect colors having a gain of zero. <br> <br>Note: This call will override any CCA settings performed by prior calls. <br>"
    global Summary
    Summary.Command = "Write Image Hsg"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',121))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgRedGain,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgRedSaturation,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgRedHue,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgGreenGain,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgGreenSaturation,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgGreenHue,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgBlueGain,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgBlueSaturation,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgBlueHue,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgCyanGain,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgCyanSaturation,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgCyanHue,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgMagentaGain,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgMagentaSaturation,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgMagentaHue,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgYellowGain,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgYellowSaturation,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgYellowHue,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgWhiteRedGain,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgWhiteGreenGain,16384)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ImageHsg.HsgWhiteBlueGain,16384)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImageHsg():
    "This command returns the currently applied hue, saturation and gain values for all the colors. If gain for a color is zero then the HSG is not applied on the color. <br>"
    global Summary
    Summary.Command = "Read Image Hsg"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',121))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(42, writebytes, ProtocolData)
        ImageHsg.HsgRedGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 0)[0], 16384)
        ImageHsg.HsgRedSaturation = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 2)[0], 16384)
        ImageHsg.HsgRedHue = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 4)[0], 16384)
        ImageHsg.HsgGreenGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 6)[0], 16384)
        ImageHsg.HsgGreenSaturation = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 8)[0], 16384)
        ImageHsg.HsgGreenHue = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 10)[0], 16384)
        ImageHsg.HsgBlueGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 12)[0], 16384)
        ImageHsg.HsgBlueSaturation = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 14)[0], 16384)
        ImageHsg.HsgBlueHue = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 16)[0], 16384)
        ImageHsg.HsgCyanGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 18)[0], 16384)
        ImageHsg.HsgCyanSaturation = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 20)[0], 16384)
        ImageHsg.HsgCyanHue = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 22)[0], 16384)
        ImageHsg.HsgMagentaGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 24)[0], 16384)
        ImageHsg.HsgMagentaSaturation = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 26)[0], 16384)
        ImageHsg.HsgMagentaHue = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 28)[0], 16384)
        ImageHsg.HsgYellowGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 30)[0], 16384)
        ImageHsg.HsgYellowSaturation = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 32)[0], 16384)
        ImageHsg.HsgYellowHue = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 34)[0], 16384)
        ImageHsg.HsgWhiteRedGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 36)[0], 16384)
        ImageHsg.HsgWhiteGreenGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 38)[0], 16384)
        ImageHsg.HsgWhiteBlueGain = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 40)[0], 16384)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ImageHsg

def WriteImageCcaHsgEnableMode(CcaHsgEnable,  CurrentPccAlgorithm):
    "This command sets the PCC hardware Enable Mode which is needed by CCA/HSG. <br>"
    global Summary
    Summary.Command = "Write Image Cca Hsg Enable Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',123))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(CcaHsgEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        writebytes.extend(list(struct.pack('B',CurrentPccAlgorithm.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImageCcaHsgEnableMode():
    "This command sets the PCC hardware Enable Mode which is needed by CCA/HSG. <br>"
    global Summary
    Summary.Command = "Read Image Cca Hsg Enable Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',123))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        CcaHsgEnable = getbits(1, 0);
        CurrentPccAlgorithmObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, CcaHsgEnable, CmdPccAlgorithmT(CurrentPccAlgorithmObj)

def WriteWpcLedCalibrationMatrix(WpcLedCalibrationMatrix):
    "This command sets the pre-computed LED calibration matrix. <br>"
    global Summary
    Summary.Command = "Write Wpc Led Calibration Matrix"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',124))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix0,1.073742E+09)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix1,1.073742E+09)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix2,1.073742E+09)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix3,1.073742E+09)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix4,1.073742E+09)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix5,1.073742E+09)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix6,1.073742E+09)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix7,1.073742E+09)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcLedCalibrationMatrix.CalibrationMatrix8,1.073742E+09)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadWpcLedCalibrationMatrix():
    "This command returns the pre-computed LED calibration matrix. <br>"
    global Summary
    Summary.Command = "Read Wpc Led Calibration Matrix"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',124))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(36, writebytes, ProtocolData)
        WpcLedCalibrationMatrix.CalibrationMatrix0 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 0)[0], 1.073742E+09)
        WpcLedCalibrationMatrix.CalibrationMatrix1 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 4)[0], 1.073742E+09)
        WpcLedCalibrationMatrix.CalibrationMatrix2 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 8)[0], 1.073742E+09)
        WpcLedCalibrationMatrix.CalibrationMatrix3 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 12)[0], 1.073742E+09)
        WpcLedCalibrationMatrix.CalibrationMatrix4 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 16)[0], 1.073742E+09)
        WpcLedCalibrationMatrix.CalibrationMatrix5 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 20)[0], 1.073742E+09)
        WpcLedCalibrationMatrix.CalibrationMatrix6 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 24)[0], 1.073742E+09)
        WpcLedCalibrationMatrix.CalibrationMatrix7 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 28)[0], 1.073742E+09)
        WpcLedCalibrationMatrix.CalibrationMatrix8 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 32)[0], 1.073742E+09)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, WpcLedCalibrationMatrix

def WriteWpcSensorCalibrationMatrix(WpcSensorCalibrationMatrix):
    "This command sets the pre-computed sensor calibration matrix. <br>"
    global Summary
    Summary.Command = "Write Wpc Sensor Calibration Matrix"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',125))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix0,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix1,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix2,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix3,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix4,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix5,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix6,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix7,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(WpcSensorCalibrationMatrix.CalibrationMatrix8,8388608)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadWpcSensorCalibrationMatrix():
    "This command gets the sensor calibration matrix. <br>"
    global Summary
    Summary.Command = "Read Wpc Sensor Calibration Matrix"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',125))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(36, writebytes, ProtocolData)
        WpcSensorCalibrationMatrix.CalibrationMatrix0 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 0)[0], 8388608)
        WpcSensorCalibrationMatrix.CalibrationMatrix1 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 4)[0], 8388608)
        WpcSensorCalibrationMatrix.CalibrationMatrix2 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 8)[0], 8388608)
        WpcSensorCalibrationMatrix.CalibrationMatrix3 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 12)[0], 8388608)
        WpcSensorCalibrationMatrix.CalibrationMatrix4 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 16)[0], 8388608)
        WpcSensorCalibrationMatrix.CalibrationMatrix5 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 20)[0], 8388608)
        WpcSensorCalibrationMatrix.CalibrationMatrix6 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 24)[0], 8388608)
        WpcSensorCalibrationMatrix.CalibrationMatrix7 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 28)[0], 8388608)
        WpcSensorCalibrationMatrix.CalibrationMatrix8 = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 32)[0], 8388608)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, WpcSensorCalibrationMatrix

def WriteWpcTargetManualMode(Enable):
    "<br>This command enables WPC Target Manual mode to use WPC Target Manual Color Point at run-time. <br> When this mode is enabled, all target color points specified in the project will be ignored. Software will set only the user specified target manual color point until the manual mode is reset using this same command. <br>"
    global Summary
    Summary.Command = "Write Wpc Target Manual Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',135))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadWpcTargetManualMode():
    "This command returns whether WPC Target Manual mode is enabled. <br>"
    global Summary
    Summary.Command = "Read Wpc Target Manual Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',135))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable

def WriteWpcTargetManualColorPoint(X,  Y):
    "<br>This command sets the target color point which will be used in WPC Target Manual Mode. <br>"
    global Summary
    Summary.Command = "Write Wpc Target Manual Color Point"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',136))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(X,32768)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(Y,32768)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadWpcTargetManualColorPoint():
    "This command gets the target color point which will be used in WPC Target Manual Mode. <br>"
    global Summary
    Summary.Command = "Read Wpc Target Manual Color Point"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',136))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        X = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 0)[0], 32768)
        Y = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 2)[0], 32768)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, X, Y

def ReadWpcTargetColorPoint():
    "This command reads the target white point color coordinates. <br> <br>Values returned give the current target white point by the algorithm. The target white point for each Look is set in the firmware. Use command Get Look to read the target white point for the active Look.  <br> <br>"
    global Summary
    Summary.Command = "Read Wpc Target Color Point"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',137))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        ChromaticX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 0)[0], 32768)
        ChromaticY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 2)[0], 32768)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ChromaticX, ChromaticY

def ReadWpcSystemColorPoint():
    "This command reads the white point color coordinates as derived from embedded light sensor data. <br> <br>Before reading the white point with this command, WPC Sensor Calibration Data must be available.  <br> The target white point for each Look is set in the firmware. Use command Get WPC Target Color Point or Get Look to read the target white point for the active Look.  <br> <br>"
    global Summary
    Summary.Command = "Read Wpc System Color Point"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',138))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(6, writebytes, ProtocolData)
        ChromaticX = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 0)[0], 32768)
        ChromaticY = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 2)[0], 32768)
        LuminanceY = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ChromaticX, ChromaticY, LuminanceY

def WriteRgbOnlyMode(Enable):
    "This command Enable/Disable RGB Only mode. This command is only useful for color overlap system. It will mask secondary colors and will avoid all color processing related to secondary colors. <br>"
    global Summary
    Summary.Command = "Write Rgb Only Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',139))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadRgbOnlyMode():
    "This command Enable/Disable RGB Only mode <br>"
    global Summary
    Summary.Command = "Read Rgb Only Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',139))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable

def WriteCwStart(Start):
    "Start/Stop All Color wheel <br>"
    global Summary
    Summary.Command = "Write Cw Start"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',198))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Start), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadCwStart(Wheel):
    ""
    global Summary
    Summary.Command = "Read Cw Start"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',198))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Wheel.value)))
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Running = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Running

def WriteCoastMode(Enable,  SlowPhaseLock):
    "<br><br>"
    global Summary
    Summary.Command = "Write Coast Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',199))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        value = setbits(int(SlowPhaseLock), 1, 1)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadCoastMode():
    "<br><br>"
    global Summary
    Summary.Command = "Read Coast Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',199))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
        SlowPhaseLock = getbits(1, 1);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable, SlowPhaseLock

def WriteCwSpeed(Speed):
    ""
    global Summary
    Summary.Command = "Write Cw Speed"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',200))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',Speed)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadCwSpeed(Wheel):
    ""
    global Summary
    Summary.Command = "Read Cw Speed"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',200))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Wheel.value)))
        readbytes = _readcommand(8, writebytes, ProtocolData)
        Period = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
        Frequency = struct.unpack_from ('I', bytearray(readbytes), 4)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Period, Frequency

def WriteCwDualTrackMode(Mode):
    "This function sets the strength, or speed, at which the secondary color wheel will track the primary color wheel with respect to phase alignment. This function has no affect if there is only one color wheel in the system. It is recommended to start the system with either @ref CW_TRACK_NORMAL or @ref CW_TRACK_SLOW, then increase the strength as needed. @ref CW_TRACK_FAST should be used with caution as some wheels may become unstable with this setting. <br>"
    global Summary
    Summary.Command = "Write Cw Dual Track Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',201))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Mode.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadCwDualTrackMode():
    "This function gets the strength, or speed, at which the secondary color wheel will track the primary color wheel with respect to phase alignment. <br>"
    global Summary
    Summary.Command = "Read Cw Dual Track Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',201))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        ModeObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, CwMultiWheelTrackingModeT(ModeObj)

def WriteCwSpokeTestConfiguration(Enable,  SpokeNumber,  RevolutionNumber,  Mode):
    ""
    global Summary
    Summary.Command = "Write Cw Spoke Test Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',202))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        writebytes.extend(list(struct.pack('B',SpokeNumber)))
        writebytes.extend(list(struct.pack('B',RevolutionNumber)))
        writebytes.extend(list(struct.pack('B',Mode.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadCwSpokeTestConfiguration():
    ""
    global Summary
    Summary.Command = "Read Cw Spoke Test Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',202))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
        SpokeNumber = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        RevolutionNumber = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        ModeObj = struct.unpack_from ('B', bytearray(readbytes), 3)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable, SpokeNumber, RevolutionNumber, SeqSpokeTestModesT(ModeObj)

def WriteCwIndexDelay(Wheel,  DegreesInteger,  DegreesFraction):
    "This command is used to time delay the passing of the color wheel index signal inside the ASIC.  If the color wheel index generation is accomplished with a stripe on the hub of the motor, the relationship of the stripe to the first color may be skewed.  This command can be used to attempt to correct this skew by repositioning the index electronically. <br>"
    global Summary
    Summary.Command = "Write Cw Index Delay"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',203))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Wheel.value)))
        writebytes.extend(list(struct.pack('H',DegreesInteger)))
        writebytes.extend(list(struct.pack('B',DegreesFraction)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadCwIndexDelay(Wheel):
    "Gets the time delay of the skewed colorwheel index <br>"
    global Summary
    Summary.Command = "Read Cw Index Delay"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',203))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Wheel.value)))
        readbytes = _readcommand(3, writebytes, ProtocolData)
        DegreesInteger = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        DegreesFraction = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DegreesInteger, DegreesFraction

def WriteCwDebugMode(Enable):
    "<br>"
    global Summary
    Summary.Command = "Write Cw Debug Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',204))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadCwDebugMode():
    "<br>"
    global Summary
    Summary.Command = "Read Cw Debug Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',204))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable

def WriteExecuteDisplay():
    "This command initiates the execution of queued display commands.<br> Due to an extended setup and reconfiguration time, some display commands have been made into queued commands. This means that the commands will not be executed until the Execute Display Command is called. Grouping multiple queued commands allows for a reduced configuration time.<br> <br>The queued commands include but are not limited to:<br> 1. Set Input Image Size Queued<br> 2. Set Image Crop Queued<br> 3. Set Display Size Queued<br> 4. Set Pre-Defined Timings Queued<br> 5. Any XPR control commands<br> 6. Set VBO Configuration<br> 7. Write Splash Screen Select<br> <br>It is recommended to follow this command with Read Execute Display Status to confirm that this has been executed without error.<br> <br>"
    global Summary
    Summary.Command = "Write Execute Display"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',225))
        ProtocolData.OpcodeLength = 1;
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadExecuteDisplayStatus():
    "This command returns the status of the previous Execute Display command. <br>"
    global Summary
    Summary.Command = "Read Execute Display Status"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',226))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(3, writebytes, ProtocolData)
        ExecuteCommandStateObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        ErrorCodeObj = struct.unpack_from ('H', bytearray(readbytes), 1)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DispExecuteCommandStateT(ExecuteCommandStateObj), ErrCodeT(ErrorCodeObj)

def WriteInputImageSizeQueued(PixelsPerLine,  LinesPerFrame):
    "<br>This command specifies the active data size of the internal/external input image to the controller.<br> <br>The parameter values are 1-based (for example, a value of 1280 pixels specifies 1280 pixels per line).<br> <br>This command must be followed with a Write Execute Display command to be applied. <br>"
    global Summary
    Summary.Command = "Write Input Image Size Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',227))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',PixelsPerLine)))
        writebytes.extend(list(struct.pack('H',LinesPerFrame)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadInputImageSizeQueued():
    "This command returns currently set internal/external input image size. <br>"
    global Summary
    Summary.Command = "Read Input Image Size Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',227))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        PixelsPerLine = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        LinesPerFrame = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, PixelsPerLine, LinesPerFrame

def WriteImageCropQueued(CropStartPixel,  CropStartLine,  PixelsPerLine,  LinesPerFrame):
    "<br>This command specifies the cropping applied to input images.<br> <br>This command applies to all sources including test patterns, splash screens, and external sources.<br> <br>Cropping is done prior to the scaling function in the controller. As such, the size difference between the cropped image size and displayed image size determines the amount of scaling needed in both dimensions if scaling using WRP is enabled.<br> <br>This command must be followed with a Write Execute Display command to be applied.<br> <br>"
    global Summary
    Summary.Command = "Write Image Crop Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',228))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',CropStartPixel)))
        writebytes.extend(list(struct.pack('H',CropStartLine)))
        writebytes.extend(list(struct.pack('H',PixelsPerLine)))
        writebytes.extend(list(struct.pack('H',LinesPerFrame)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImageCropQueued():
    "This command returns the cropping applied to input images prior to controller image processing. <br>"
    global Summary
    Summary.Command = "Read Image Crop Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',228))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(8, writebytes, ProtocolData)
        CropStartPixel = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        CropStartLine = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        PixelsPerLine = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
        LinesPerFrame = struct.unpack_from ('H', bytearray(readbytes), 6)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, CropStartPixel, CropStartLine, PixelsPerLine, LinesPerFrame

def WriteDisplaySizeQueued(PixelsPerLine,  LinesPerFrame):
    "This command specifies the active image resolution to be output on the display module, specifies the size of the non-keystone corrected, non-warped image to be output from the scalar function. This is the resolution of the rectangular or square displayed image. The controller will determine the amount of scaling needed in x and in y based on the size of the input image. For a source image from the external video port, the controller will measure the size of the source image based on the DATEN signal. However, if the image is cropped by command Set Image Crop, the controller will use this smaller size to be scaled to fill the DMD.<br> <br>The parameter values are to be 1-based such that a value of 1280 pixels displays 1280 pixels per line.<br> <br>If keystone correction or warping is enabled, the resulting non-rectangular images on the DMD will all fit within the active display region specified by command Set Display Size.<br> <br>If the display size exceeds the resolution available on the DMD, this is considered an error and the command does not execute. The display size parameters are checked against the DMD available resolution in both rotation image orientations (non-rotated and rotated), and if the DMD resolution is exceeded in either of these orientations, it is considered an error. The system does not check for proper image orientation setup.<br> <br>If the source, crop, and display parameter combinations exceed the capabilities of the scalar, the system implements the user request as best it can, and the displayed image may be broken. The user must provide updated parameters to fix the image.<br> <br>This command must be followed with a Write Execute Display command to be applied. <br>"
    global Summary
    Summary.Command = "Write Display Size Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',229))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',PixelsPerLine)))
        writebytes.extend(list(struct.pack('H',LinesPerFrame)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDisplaySizeQueued():
    "This command returns the size of the active image display size. <br>"
    global Summary
    Summary.Command = "Read Display Size Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',229))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        PixelsPerLine = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        LinesPerFrame = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, PixelsPerLine, LinesPerFrame

def WriteDisplayImageOrientationQueued(LongAxisImageFlip,  ShortAxisImageFlip):
    "<br>This command specifies the orientation of the image displayed on the DMD.<br> <br>The command rotates and/or flips the image displayed on the DMD. Rotation can be useful for a portrait source image such as inside a mobile phone. Flips are provided to support ceiling mount and rear projection use cases.<br> <br>Landscape images typically should not be rotated, but the controller allows this as it may be appropriate for some situations or configurations.<br> <br>Image rotation is allowed while keystone correction or warping is enabled, though it may not be appropriate for all situations or configurations.<br> <br>The user is responsible for determining if the resulting image from these commands is acceptable.<br> <br>User can use the Display Size command to centre the image. <br> <br>This command must be followed with a Write Execute Display command to be applied. <br>"
    global Summary
    Summary.Command = "Write Display Image Orientation Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',230))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(LongAxisImageFlip), 1, 1)
        value = setbits(int(ShortAxisImageFlip), 1, 2)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDisplayImageOrientationQueued():
    "Data returned is in the same format as Write Parameters for command Set Display Image Orientation. <br>"
    global Summary
    Summary.Command = "Read Display Image Orientation Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',230))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        LongAxisImageFlip = getbits(1, 1);
        ShortAxisImageFlip = getbits(1, 2);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, LongAxisImageFlip, ShortAxisImageFlip

def WriteDisplayCurtain(CurtainEnable,  CurtainColor):
    "<br>This command controls the image curtain displayed on the DMD. <br>The image curtain fills the entire DMD with a user-specified color. The color specified for the curtain by this command is separate from the border color defined by command Set Border Color.   <br> <br>Please note that scaling or cropped images may affect the border color. <br>"
    global Summary
    Summary.Command = "Write Display Curtain"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',231))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(CurtainEnable), 1, 0)
        value = setbits(CurtainColor.value, 3, 1)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDisplayCurtain():
    "Data returned is in the same format as Write Parameters for command Display Curtain. <br>"
    global Summary
    Summary.Command = "Read Display Curtain"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',231))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        CurtainEnable = getbits(1, 0);
        CurtainColorObj = getbits(3, 1);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, CurtainEnable, DispCurtainColorT(CurtainColorObj)

def WriteImageFreeze(ImageFreeze):
    "<br>This command freezes the image whereby the last image received is displayed in every subsequent frame. <br>The image freeze capability has two main uses. The first use is to simply freeze the current image on the screen. The second use is to assist the user in reducing display artifacts during limited system configuration changes. In this second case, the image is frozen, system changes are made, and the image is unfrozen after completion. When the image is unfrozen, the display shows the most recent input image frames. Input data between the freeze point and the unfreeze point is lost. However, due to the possibility of commands that affect the DMD immediately, it is recommended to disabled LED's during transitions. <br><br> The controller software does not freeze or unfreeze the image except when explicitly commanded to by command Set Image Freeze. This is true whether controller software is making updates to the system on its own volition or during any operation commanded via the I2C interface. <br> An overview of using the Set Image Freeze command is included.    <br> <br>Use of Image Freeze to Reduce On-Screen Artifacts :  <br> <br>Commands that take a long time to process, require a lot a data to be loaded from flash, or change the frame timing of the system may create on-screen artifacts. The Set Image Freeze command can minimize or eliminate these artifacts. The process is: <br> 1. Send a Set Image Freeze command to enable    <br> 2. Send commands with the potential to create image <br> 3. Send a Set Image Freeze command to disable   <br> <br>Because commands to the controller process serially, no special timing or delay is required between these commands. The number of commands placed between the freeze and unfreeze should be small, as it is not desirable for the image to be frozen for a long period of time. Caution: Command Set Display Curtain or any operation that requires curtain will override Freeze and the frozen displayed image will be lost. The following operations require a curtain and will override Freeze:   <br> 1. Source Type Switch (Standard - XPR - 3D) <br> 2. Switch to Splash display <br> 3. Source Re-lock    <br> 4. Switch to Standby Mode   <br> <br>"
    global Summary
    Summary.Command = "Write Image Freeze"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',232))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(ImageFreeze), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImageFreeze():
    "Data returned is in the same format as Write Parameters for command Set Image Freeze. <br>"
    global Summary
    Summary.Command = "Read Image Freeze"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',232))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        ImageFreeze = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ImageFreeze

def WriteBorderColor(DisplayBorderColor):
    "<br>This command specifies the border color displayed on the DMD. <br>Whenever a displayed image is smaller than the active mirror array on the DMD, the border color is used for all non-image pixels. Some examples using a border include a window box, pillar box, and letterbox image. <br>"
    global Summary
    Summary.Command = "Write Border Color"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',233))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(DisplayBorderColor.value, 3, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadBorderColor():
    "Data returned is in the same format as Write Parameters for command Set Border Color. <br>"
    global Summary
    Summary.Command = "Read Border Color"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',233))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        DisplayBorderColorObj = getbits(3, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DispCurtainColorT(DisplayBorderColorObj)

def WriteLedEnable(Red,  Green,  Blue):
    "This command enables or disables the individual LED Channels. <br>"
    global Summary
    Summary.Command = "Write Led Enable"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',208))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Red), 1, 0)
        value = setbits(int(Green), 1, 1)
        value = setbits(int(Blue), 1, 2)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadLedEnable():
    "This command returns if the LED Channels are enabled or disabled. <br>"
    global Summary
    Summary.Command = "Read Led Enable"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',208))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Red = getbits(1, 0);
        Green = getbits(1, 1);
        Blue = getbits(1, 2);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Red, Green, Blue

def WriteLedCurrents(LedCurrents):
    "This command sets the drive levels for each LED. The drive levels are set only if the LED Channel is valid. <br>The currents for each individual LED can be controlled independently. The limits for the current level set is decided by the minimum and maximum values specified for the system in the flash image. The command will not return an error if the current is outside the expected range. Instead, it will automatically limits to minimum limit if the value is less then the minimum limit and limits to maximum limit if the value is greater then the maximum limit. Reading back the values will guarantee whether it is applied directly or limited against the minimum and maximum. The applicable LED must be enabled for the effect to be seen on the display. <br> <br>When the color processing algorithms (WPC and Dynamic Black) are disabled, this command directly sets the LED currents (the R, G, and B 10-bit values provided are sent directly to the DLPA PMIC by the controller via SPI). If color processing algorithm is enabled, then this command will not take effect immediately. <br> <br>When an all-white image is displayed and color processing algorithms are disabled, this command allows the system white point to be adjusted while at the same time establishing the total LED power for the display module. <br>"
    global Summary
    Summary.Command = "Write Led Currents"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',209))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',LedCurrents.RedLevel)))
        writebytes.extend(list(struct.pack('H',LedCurrents.GreenLevel)))
        writebytes.extend(list(struct.pack('H',LedCurrents.BlueLevel)))
        writebytes.extend(list(struct.pack('H',LedCurrents.YellowLevel)))
        writebytes.extend(list(struct.pack('H',LedCurrents.CyanLevel)))
        writebytes.extend(list(struct.pack('H',LedCurrents.MagentaLevel)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadLedCurrents():
    "This command gets the drive levels for each LED. <br>"
    global Summary
    Summary.Command = "Read Led Currents"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',209))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(12, writebytes, ProtocolData)
        LedCurrents.RedLevel = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        LedCurrents.GreenLevel = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        LedCurrents.BlueLevel = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
        LedCurrents.YellowLevel = struct.unpack_from ('H', bytearray(readbytes), 6)[0]
        LedCurrents.CyanLevel = struct.unpack_from ('H', bytearray(readbytes), 8)[0]
        LedCurrents.MagentaLevel = struct.unpack_from ('H', bytearray(readbytes), 10)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, LedCurrents

def WriteLedMaxCurrents(LedMaxCurrents):
    "<br>This command specifies the maximum 10-bit current allowed for each LED in the display module. <br>This command sets the maximum LED currents that can be used when DB is enabled or disabled. When DB is enabled, the maximum LED currents may be further limited by the DB intensity-to-current LUTs stored in flash. <br>This command protects the LEDs from a user accidently setting LED currents higher than the system can handle when using command Set RGB LED Currents. <br>"
    global Summary
    Summary.Command = "Write Led Max Currents"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',213))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',LedMaxCurrents.Red)))
        writebytes.extend(list(struct.pack('H',LedMaxCurrents.Green)))
        writebytes.extend(list(struct.pack('H',LedMaxCurrents.Blue)))
        writebytes.extend(list(struct.pack('H',LedMaxCurrents.Yellow)))
        writebytes.extend(list(struct.pack('H',LedMaxCurrents.Cyan)))
        writebytes.extend(list(struct.pack('H',LedMaxCurrents.Magenta)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadLedMaxCurrents():
    "Data returned is in the same format as Write Parameters for command Set RGB LED Max Currents. <br>"
    global Summary
    Summary.Command = "Read Led Max Currents"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',213))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(12, writebytes, ProtocolData)
        LedMaxCurrents.Red = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        LedMaxCurrents.Green = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        LedMaxCurrents.Blue = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
        LedMaxCurrents.Yellow = struct.unpack_from ('H', bytearray(readbytes), 6)[0]
        LedMaxCurrents.Cyan = struct.unpack_from ('H', bytearray(readbytes), 8)[0]
        LedMaxCurrents.Magenta = struct.unpack_from ('H', bytearray(readbytes), 10)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, LedMaxCurrents

def ReadLedMinCurrents():
    "<br>This command returns the minimum current allowed for each LED in the display module. <br>"
    global Summary
    Summary.Command = "Read Led Min Currents"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',214))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(12, writebytes, ProtocolData)
        LedMinCurrents.Red = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        LedMinCurrents.Green = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        LedMinCurrents.Blue = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
        LedMinCurrents.Yellow = struct.unpack_from ('H', bytearray(readbytes), 6)[0]
        LedMinCurrents.Cyan = struct.unpack_from ('H', bytearray(readbytes), 8)[0]
        LedMinCurrents.Magenta = struct.unpack_from ('H', bytearray(readbytes), 10)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, LedMinCurrents

def WriteDynamicBlackEnable(Enable):
    "This command specifies the Dynamic Black enable or disable. <br>When Dynamic Black is enabled, LED currents are controlled automatically and Set LED Currents command connot be used to set currents. Commands supported in each mode are shown below. <br>Dynamic Black disabled - Set RGB LED Enable, Get RGB LED Enable, Set RGB LED Currents, Get RGB LED Currents, Set RGB LED Max Currents, Get RGB LED Max Currents, Get RGB LED Min Currents <br> <br>Dynamic Black enabled - Set RGB LED Enable, Get RGB LED Enable, Get RGB LED Currents, Set RGB LED Max Currents, Get RGB LED Max Currents, Get RGB LED Min Currents.<br> <br>Note that the Dynamic Black commands will take precedence over other color processing algorithms and that dynamic content is needed for this algorithm to work. DB will not have any affect on static images such as splash screen. <br>"
    global Summary
    Summary.Command = "Write Dynamic Black Enable"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',210))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDynamicBlackEnable():
    "Data returned is in the same format as Write Parameters for command Set Dynamic Black Enable. <br>"
    global Summary
    Summary.Command = "Read Dynamic Black Enable"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',210))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
        CurrentDbStatus = getbits(1, 1);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable, CurrentDbStatus

def WriteImagePixelBrightness(Brightness):
    "This command controls the pixel brightness by providing an additive gain to each pixel. The brightness value specified affects the red, green and blue components uniformly. For YCbCr images, brightness setting is applied after it is converted to RGB. <br>"
    global Summary
    Summary.Command = "Write Image Pixel Brightness"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',246))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('h',Brightness)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImagePixelBrightness():
    "This command returns the currently applied Image Brightness value (offset applied to pixel values). The offset added to red, green, and blue is same. Brightness is applied on YCbCr images after converting it to RGB. <br>"
    global Summary
    Summary.Command = "Read Image Pixel Brightness"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',246))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        Brightness = struct.unpack_from ('h', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Brightness

def WriteImagePixelContrast(Contrast):
    "This command controls the pixel contrast by providing a multiplicative gain to each pixel. The contrast value specified affects the red, green and blue components uniformly. For YCbCr images, contrast setting is applied after it is converted to RGB. <br>"
    global Summary
    Summary.Command = "Write Image Pixel Contrast"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',247))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Contrast)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImagePixelContrast():
    "This command returns the currently applied Image Contrast value (gain multiplied to pixel values). The gain is same for red, green, and blue. Contrast is applied on YCbCr images after converting it to RGB. <br>"
    global Summary
    Summary.Command = "Read Image Pixel Contrast"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',247))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        Contrast = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Contrast

def WriteDegammaTable(TableIndex):
    "This command specifies the degamma look-up table (LUT) to be used when displaying images. This command causes the degamma table for given index to be read from flash memory and loaded into the controller's internal degamma LUT. <br>The table indexes are 0-based (starting from 0). The maximum value can be 254. A value of 255 would disable de-gamma operations. <br>"
    global Summary
    Summary.Command = "Write Degamma Table"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',248))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',TableIndex)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDegammaTable():
    "This command returns currently applied degamma table. <br>"
    global Summary
    Summary.Command = "Read Degamma Table"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',248))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        TableIndex = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TableIndex

def WriteImageSharpness(Sharpness):
    "This command configures the sharpness filter. A value of 0 is the least sharp (smoothest), while a value of 31 is the sharpest. This filter is in the back end of the data path, so both video and graphics are affected. TI recommends that the sharpness filters be disabled (sharpness=16) for graphics sources. <br>"
    global Summary
    Summary.Command = "Write Image Sharpness"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',249))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Sharpness)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImageSharpness():
    "The command returns the current sharpness value. <br>"
    global Summary
    Summary.Command = "Read Image Sharpness"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',249))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        Sharpness = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Sharpness

def WriteImageCscIndexValue(CscIndexValue,  UserCscEnable):
    "This command controls the applied CSC matrix by setting the currently applied CSC matrix index. All indices can be populated as defined by the customer in the flash. <br><br>"
    global Summary
    Summary.Command = "Write Image Csc Index Value"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',250))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',CscIndexValue)))
        packerinit()
        value = setbits(int(UserCscEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadImageCscIndexValue():
    "<br>This command returns the currently applied CSC matrix index. <br>"
    global Summary
    Summary.Command = "Read Image Csc Index Value"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',250))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        CscIndexValue = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        readdata = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        packerinit(readdata)
        UserCscEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, CscIndexValue, UserCscEnable

def WriteXprFilterStrengthCommand(Strength):
    "This commands sets the XPR filter segment length. <br> <br>For more information regarding filter segment length, please refer to the actuator user's guide or contact your actuator manufacturer. <br><br>"
    global Summary
    Summary.Command = "Write Xpr Filter Strength Command"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',251))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Strength)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadXprFilterStrengthCommand():
    "This commands returns the XPR filter segment length. <br> <br><br>"
    global Summary
    Summary.Command = "Read Xpr Filter Strength Command"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',251))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        Strength = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Strength

def WriteUserSettingsCommitMode(CommitMode):
    "This command is used to switch between the commit modes - immediate and update via command, during run-time. This command is only applicable if data storage mode is EEPROM. In Immediate mode data will be stored in EEPROM as it is updated. In Command mode updated data will be only stored once the Commit Data command is given. <br>"
    global Summary
    Summary.Command = "Write User Settings Commit Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',146))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',CommitMode.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadUserSettingsCommitMode():
    "This command returns the current user settings commit mode. <br>"
    global Summary
    Summary.Command = "Read User Settings Commit Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',146))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        CommitModeObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DataCommitMode(CommitModeObj)

def WriteUseFactoryDefaultsOnNextPowerUp(UseFactoryDefault):
    "<br>When this flag is set, the default factory settings  are applied on next power-up without invalidating (erasing) the settings stored in the EEPROM/Flash. Upon power up, change in any setting will not be updated to the EEPROM/Flash irrespective of commit mode. If Data Storage mode is EEPROM and commit mode is immediate, setting this flag will restart the system immediately. If data storage is Flash, the Commit Data command needs to be given and system will not start restart immediately. <br>"
    global Summary
    Summary.Command = "Write Use Factory Defaults On Next Power Up"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',147))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(UseFactoryDefault), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteUpdateLockState(DataManagerUpdatesDisabled):
    "<br>This command sets the current data update lock state for EEPROM/FLASH. <br>When lock is set, all writes to EEPROM/Flash settings and/or calibration data from application software will not be actually written to the EEPROM/Flash. The locked mode is to be used only in factory where user wants to play around with various settings without actually recording them in the EEPROM/Flash. In Normal Use mode, the lock is not supposed to be set. <br>"
    global Summary
    Summary.Command = "Write Update Lock State"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',148))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(DataManagerUpdatesDisabled), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadUpdateLockState():
    "<br>This command returns the current data update lock state for EEPROM/FLASH. <br>"
    global Summary
    Summary.Command = "Read Update Lock State"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',148))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        DataManagerUpdatesDisabled = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DataManagerUpdatesDisabled

def WriteCommitDisplayWarpKeystoneParams(CommitDisplayParams,  CommitWarpParams,  CommitKeystoneParams,  WarpMapIndex):
    "This command commits display, warp, and keystone parameters to EEPROM. In order for this function to work properly, the storage mode should be EEPROM, the execute display status should not be in progress, and the commit mode should be immediate. When storage mode is FLASH, please use 'WriteCommitData' to commit changes. If the function fails, there is a possibility that only partial data may be written to EEPROM. To avoid having partially written display settings in EEPROM, the user needs to reattempt this function after addressing the error cause. <br>"
    global Summary
    Summary.Command = "Write Commit Display Warp Keystone Params"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',149))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(CommitDisplayParams), 1, 0)
        value = setbits(int(CommitWarpParams), 1, 1)
        value = setbits(int(CommitKeystoneParams), 1, 2)
        writebytes.extend(list(struct.pack('B',value)))
        writebytes.extend(list(struct.pack('B',WarpMapIndex)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteEepromScratchpadMemory(Index,  Size,  Data):
    "This command writes data to EEPROM connected to the controller. <br> The EEPROM holds settings, calibration data and Scratchpad. The primary purpose of this function is for the user to write to areas of EEPROM outside of the settings and calibration data (i.e to the Scratchpad area). <br>"
    global Summary
    Summary.Command = "Write Eeprom Scratchpad Memory"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',152))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',Index)))
        writebytes.extend(list(struct.pack('H',Size)))
        if Size:
            writebytes.extend(list(Data))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadEepromScratchpadMemory(Index,  Size):
    "This function reads data from the Scratchpad in EEPROM connected to the controller. Size should be greater than 0 otherwise the command will fail. <br>"
    global Summary
    Summary.Command = "Read Eeprom Scratchpad Memory"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',152))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',Index)))
        writebytes.extend(list(struct.pack('H',Size)))
        readbytes = _readcommand(Size, writebytes, ProtocolData)
        Data = bytearray(readbytes)[0, 1]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Data

def WriteDataInvalidate(DataInvalidate):
    "This command invalidates the user settings portion of EEPROM data or calibration portion of EEPROM data or both as per input arguments and restarts the system. If none of the settings or calibration data is selected, then the command does nothing. <br>"
    global Summary
    Summary.Command = "Write Data Invalidate"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',153))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(DataInvalidate.InvalidateUserSettings), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        packerinit()
        value = setbits(int(DataInvalidate.InvalidateSsiCalibrationData), 1, 0)
        value = setbits(int(DataInvalidate.InvalidateWpcCalibrationData), 1, 1)
        value = setbits(int(DataInvalidate.InvalidateWpcCalibrationMatrixData), 1, 2)
        value = setbits(int(DataInvalidate.InvalidateXprCalibrationData), 1, 3)
        value = setbits(int(DataInvalidate.InvalidateXprWaveformCalibrationData), 1, 4)
        value = setbits(int(DataInvalidate.InvalidateWarpMapData), 1, 5)
        value = setbits(int(DataInvalidate.InvalidateCwLampData), 1, 6)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteCommitData():
    "If data storage mode is EEPROM, then calibration data is written immediately irrespective of Commit Mode. But if commit mode is Command, then user settings will be only stored in eeprom on passing this command. If data storage mode is Flash, then there is no Immediate Commit mode. User setting and calibration data will be only stored when a command is given."
    global Summary
    Summary.Command = "Write Commit Data"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',154))
        ProtocolData.OpcodeLength = 1;
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDataOperationsStatus():
    "The command returns the current working status of EEPROM/flash. <br><br>"
    global Summary
    Summary.Command = "Read Data Operations Status"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',155))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(10, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        DataOperationsStatus.DataUpdateIsDisabled = getbits(1, 0);
        DataOperationsStatus.UseFactoryDefault = getbits(1, 1);
        DataOperationsStatus.ScratchpadAreaOffset = struct.unpack_from ('H', bytearray(readbytes), 1)[0]
        DataOperationsStatus.AvailableScartchpadArea = struct.unpack_from ('I', bytearray(readbytes), 3)[0]
        readdata = struct.unpack_from ('B', bytearray(readbytes), 7)[0]
        packerinit(readdata)
        DataOperationsStatus.CommunicationWithEepromSuccessful = getbits(1, 0);
        DataOperationsStatus.DataStorageMode = struct.unpack_from ('B', bytearray(readbytes), 8)[0]
        readdata = struct.unpack_from ('B', bytearray(readbytes), 9)[0]
        packerinit(readdata)
        DataOperationsStatus.UpdatedDataCommitPending = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DataOperationsStatus

def ReadDmdTemperature(TemperatureSensorType):
    "This command is applicable only if TMP411A temperature sensor is installed in the system. If properly configured, the thermistor should not return a negative value.<br> <br>A local reading means that the reading is directly at the TMP411. A remote reading would mean that the reading is taking place at the test point pins of the DMD (indirectly at the DMD). <br>"
    global Summary
    Summary.Command = "Read Dmd Temperature"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',156))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',TemperatureSensorType.value)))
        readbytes = _readcommand(2, writebytes, ProtocolData)
        Temperature = struct.unpack_from ('h', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Temperature

def WriteCalibrationData(CalibrationDataBlock,  Size,  OffsetFromStartOfCalibBlock,  Data):
    "This command sets the Calibration data for the selected block. <br>"
    global Summary
    Summary.Command = "Write Calibration Data"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',157))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',CalibrationDataBlock.value)))
        writebytes.extend(list(struct.pack('H',Size)))
        writebytes.extend(list(struct.pack('H',OffsetFromStartOfCalibBlock)))
        if Size:
            writebytes.extend(list(Data))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadCalibrationData(CalibrationDataBlock,  Size,  OffsetFromStartOfCalibBlock):
    "This command sets the Calibration data for the selected block. <br>"
    global Summary
    Summary.Command = "Read Calibration Data"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',157))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',CalibrationDataBlock.value)))
        writebytes.extend(list(struct.pack('H',Size)))
        writebytes.extend(list(struct.pack('H',OffsetFromStartOfCalibBlock)))
        readbytes = _readcommand(Size, writebytes, ProtocolData)
        Data = bytearray(readbytes)[0, 1]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Data

def WritePwmFanControl(Gpio28IrFrequency,  Gpio29UvFrequency,  Gpio28IrDutyCycle,  Gpio29UvDutyCycle,  PwmFanControlEnable):
    "This command Enables/Disables the PWM Fan Control and Sets the Frequency and Duty Cycle. <br>"
    global Summary
    Summary.Command = "Write Pwm Fan Control"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',158))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',Gpio28IrFrequency)))
        writebytes.extend(list(struct.pack('I',Gpio29UvFrequency)))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(Gpio28IrDutyCycle,256)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(Gpio29UvDutyCycle,256)))))
        packerinit()
        value = setbits(int(PwmFanControlEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadPwmFanControl():
    "This command returns if PWM Fan Control is Enabled/Disabled and the Frequency, Duty Cycle. <br>"
    global Summary
    Summary.Command = "Read Pwm Fan Control"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',158))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(13, writebytes, ProtocolData)
        Gpio28IrFrequency = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
        Gpio29UvFrequency = struct.unpack_from ('I', bytearray(readbytes), 4)[0]
        Gpio28IrDutyCycle = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 8)[0], 256)
        Gpio29UvDutyCycle = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 10)[0], 256)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 12)[0]
        packerinit(readdata)
        PwmFanControlEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Gpio28IrFrequency, Gpio29UvFrequency, Gpio28IrDutyCycle, Gpio29UvDutyCycle, PwmFanControlEnable

def ReadDataBlock(DataType,  Size,  OffsetFromStartOfDataBlock):
    "This command gets the Calibration, User Settings or Scratchpad data from eeprom/flash, if the data storage mode is eeprom it fetches data from eeprom if the data storage mode is flash it fetches data from flash (user settings data block, calibration data block). Note: The data returned here is not the default data stored in the app config struct <br>"
    global Summary
    Summary.Command = "Read Data Block"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',159))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',DataType.value)))
        writebytes.extend(list(struct.pack('H',Size)))
        writebytes.extend(list(struct.pack('H',OffsetFromStartOfDataBlock)))
        readbytes = _readcommand(Size, writebytes, ProtocolData)
        Data = bytearray(readbytes)[0, 1]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Data

def ReadIsDiscreteDutyCycleSupported():
    "This function gets information (Discrete DC enabled and Num of Discrete DCs) about currently active sequence. <br>"
    global Summary
    Summary.Command = "Read Is Discrete Duty Cycle Supported"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',87))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable

def WriteSeqEnable(Enable):
    "This command enable/disable Sequencer, if sequencer is disabled DMD will be automatically parked. When user enable sequencer, DMD will be unparked again. <br>"
    global Summary
    Summary.Command = "Write Seq Enable"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',239))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadSeqEnable():
    "This command returns if the sequencer is enabled or disabled. <br>"
    global Summary
    Summary.Command = "Read Seq Enable"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',239))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable

def WriteSystemLookIndex(LookIndex):
    "This command changes the Look of the displayed image by attempting a Write Look Select value by the user which will trigger to sequence selection. The value should be within the looks specified in the firmware image.<br> <br>It is recommended to add a delay of approximately 50ms after this command if it is to be followed by a Color Duty Cycle command. <br>"
    global Summary
    Summary.Command = "Write System Look Index"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',240))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',LookIndex)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadSystemLookIndex():
    "This command returns current Look Index value for the sequence selection. <br>"
    global Summary
    Summary.Command = "Read System Look Index"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',240))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        LookIndex = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, LookIndex

def WriteColorDutyCycles(ColorDutyCycles):
    "This command defines duty cycles for illumination light colors. The input values in the u9.23 fixed point format. The lower and upper limits for the duty cycles are built into the firmware image. <br>"
    global Summary
    Summary.Command = "Write Color Duty Cycles"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',241))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(ColorDutyCycles.RedDutyCycle,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(ColorDutyCycles.GreenDutyCycle,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(ColorDutyCycles.BlueDutyCycle,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(ColorDutyCycles.CyanDutyCycle,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(ColorDutyCycles.MagentaDutyCycle,8388608)))))
        writebytes.extend(list(struct.pack('I',int(convertfloattofixed(ColorDutyCycles.YellowDutyCycle,8388608)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadColorDutyCycles():
    "This command returns the duty cycles for illumination light colors. <br>"
    global Summary
    Summary.Command = "Read Color Duty Cycles"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',241))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(24, writebytes, ProtocolData)
        ColorDutyCycles.RedDutyCycle = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 0)[0], 8388608)
        ColorDutyCycles.GreenDutyCycle = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 4)[0], 8388608)
        ColorDutyCycles.BlueDutyCycle = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 8)[0], 8388608)
        ColorDutyCycles.CyanDutyCycle = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 12)[0], 8388608)
        ColorDutyCycles.MagentaDutyCycle = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 16)[0], 8388608)
        ColorDutyCycles.YellowDutyCycle = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 20)[0], 8388608)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ColorDutyCycles

def WriteDiscreteDutyCycleIndex(DutyCycleIndex):
    "This command changes the Duty Cycle which will trigger to sequence selection. The value should be within the number of discrete value specified in the firmware image. It will only be valid when Discrete DC suport is enabled with the selected source. <br>"
    global Summary
    Summary.Command = "Write Discrete Duty Cycle Index"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',242))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',DutyCycleIndex)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDiscreteDutyCycleIndex():
    "This command returns current Duty Cycle Index value for the sequence selection. The command will only be functional for discrete duty cycle entries and will not be functional for duty cycle range entries. <br>"
    global Summary
    Summary.Command = "Read Discrete Duty Cycle Index"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',242))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        DutyCycleIndex = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DutyCycleIndex

def ReadMinMaxDutyCycleSupported(Illuminator):
    "This command returns the minimum and maximum duty cycle that is supported by the selected illuminator. <br><br>"
    global Summary
    Summary.Command = "Read Min Max Duty Cycle Supported"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',244))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Illuminator.value)))
        readbytes = _readcommand(8, writebytes, ProtocolData)
        MinDutyCycle = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 0)[0], 8388608)
        MaxDutyCycle = convertfixedtofloat(struct.unpack_from ('I', bytearray(readbytes), 4)[0], 8388608)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, MinDutyCycle, MaxDutyCycle

def ReadLedIlluminationDelay(Illuminator):
    "This command returns the delay values programmed in the sequences for all the illuminators in the project. <br>"
    global Summary
    Summary.Command = "Read Led Illumination Delay"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',245))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Illuminator.value)))
        readbytes = _readcommand(8, writebytes, ProtocolData)
        EnableDelay = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        RiseTime = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        DisableDelay = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
        FallTime = struct.unpack_from ('H', bytearray(readbytes), 6)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, EnableDelay, RiseTime, DisableDelay, FallTime

def ReadInputSourceStatus():
    "This command returns the current video source and the status of the source being displayed.<br> The command indicates whether the system is displaying an internal source, if it is trying to detect an external source, if it has detected an external source, or if it is in standby mode. This command can be used by the host processor to query the status at any point in time and take the necessary action. It is expected that the host will use this command after setting up the required source and ensure that the source validity is established before setting it up for display or reading the detected timings.<br> <br>"
    global Summary
    Summary.Command = "Read Input Source Status"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',177))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        SourceObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        SystemStateObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DpDisplaySourceT(SourceObj), DpStateCommandT(SystemStateObj)

def ReadSourceTimingsAndErrors():
    "This command reads the source timings and errors for the currently selected source as detected by the hardware. For internal sources (TPG, Splash), it reports the timings as generated by the hardware. For these sources there will no timing errors as the timing selection command validates the timings before allowing user to select it. For external source this command will return the parameters as detected. Some of these parameters are directly by the hardware whereas some of them are computed in the software based on the hardware detected parameters. These are the timings as seen by the system when a source is connected. If the system detects any invalid parameter or faces any measurement error, it will report the value detected and flag the error. This command is designed to never return fail so that we can get the system detected parameters at any point of time. If system is in standby mode or in the middle of source detection, the Get Source Status Command will report this status. Under normal scenarios this command should be used only when the Get Source Status Command shows a valid source status. This command can, however, be used to check for any anomalies or errors if the Get Source status command is stuck in external source detection state.<br> <br>The horizontal and vertical back porches may be less than the front end configuration by a value of 1. This is due to Vsync width and Hsync width being extrapolated from these blankings. <br>"
    global Summary
    Summary.Command = "Read Source Timings And Errors"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',178))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(32, writebytes, ProtocolData)
        SourceTimingsAndErrors.PixelClockRate = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
        SourceTimingsAndErrors.ActivePixelsPerLine = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
        SourceTimingsAndErrors.ActiveLinesPerFrame = struct.unpack_from ('H', bytearray(readbytes), 6)[0]
        SourceTimingsAndErrors.FrameRate = struct.unpack_from ('H', bytearray(readbytes), 8)[0]
        SourceTimingsAndErrors.HSyncRate = struct.unpack_from ('I', bytearray(readbytes), 10)[0]
        SourceTimingsAndErrors.VerticalFrontPorch = struct.unpack_from ('H', bytearray(readbytes), 14)[0]
        SourceTimingsAndErrors.VerticalBackPorch = struct.unpack_from ('H', bytearray(readbytes), 16)[0]
        SourceTimingsAndErrors.VerticalSyncWidth = struct.unpack_from ('H', bytearray(readbytes), 18)[0]
        SourceTimingsAndErrors.HorizontalFrontPorch = struct.unpack_from ('H', bytearray(readbytes), 20)[0]
        SourceTimingsAndErrors.HorizontalBackPorch = struct.unpack_from ('H', bytearray(readbytes), 22)[0]
        SourceTimingsAndErrors.HorizontalSyncWidth = struct.unpack_from ('H', bytearray(readbytes), 24)[0]
        SourceTimingsAndErrors.TotalPixelsPerLine = struct.unpack_from ('H', bytearray(readbytes), 26)[0]
        SourceTimingsAndErrors.TotalLinesPerFrame = struct.unpack_from ('H', bytearray(readbytes), 28)[0]
        readdata = struct.unpack_from ('H', bytearray(readbytes), 30)[0]
        packerinit(readdata)
        SourceTimingsAndErrors.InvalidAppl = getbits(1, 0);
        SourceTimingsAndErrors.InvalidAlpf = getbits(1, 1);
        SourceTimingsAndErrors.InvalidHorizontalBlanking = getbits(1, 2);
        SourceTimingsAndErrors.InvalidVerticalBlanking = getbits(1, 3);
        SourceTimingsAndErrors.InvalidHsyncWidth = getbits(1, 4);
        SourceTimingsAndErrors.InvalidVsyncWidth = getbits(1, 5);
        SourceTimingsAndErrors.InvalidClock = getbits(1, 6);
        SourceTimingsAndErrors.UnstableTppl = getbits(1, 7);
        SourceTimingsAndErrors.UnstableActiveArea = getbits(1, 8);
        SourceTimingsAndErrors.SystemMeasurementError = getbits(1, 9);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, SourceTimingsAndErrors

def WriteEnableThreeDQueued(Enable3D,  DominantFrame):
    "This command enables the 3D image handling and sync functionality in the controller. <br>For 3D inputs to the active video port, left (L) and right (R) eye frames are input on alternate controller input frames. 3D frame inputs can be received on V-by-One. The controller receives a L/R input sync signal (on a GPIO) to identify L vs. R input frames. For 3D synchronization, there are no words to be decoded from data received over V-by-One, or FPD-Link.<br> <br>The controller stores left and right images as needed by 3D stereoscopic glasses. In these glasses, one eye sees a dark shudder while the other sees the DMD鈥檚 projected image. As images are loaded into the DMD, light from the left and right frames is sent sequentially to the screen. The controller outputs sync information to tell the glasses which image is left and which is right.<br> <br>Frame rates accepted by the controller when using DLP Link are 100+/-2Hz and 120+/-2Hz.<br> <br>When DLP Link is not used, the full range of controller input frame rates supported for non-3D applications is supported for 3D L/R frame sequential inputs. For example, the L/R frame sequential input can be 240Hz for a 1080p DMD when using a single controller.<br> <br><br>"
    global Summary
    Summary.Command = "Write Enable Three D Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',179))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable3D), 1, 0)
        value = setbits(DominantFrame.value, 2, 1)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadEnableThreeDQueued():
    "This command returns the current state of 3D image handling in the controller. <br>"
    global Summary
    Summary.Command = "Read Enable Three D Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',179))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        Enable3D = getbits(1, 0);
        DominantFrameObj = getbits(2, 1);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Enable3D, Src3DFrameDominanceT(DominantFrameObj)

def WriteExternalSourceSyncPolarity(IsManualPolarityDetection,  IsVSyncActiveHigh,  IsHSyncActiveHigh):
    "This command sets the input polarity detection mode for VSync and HSync signals for all external sources. The controller requires Sync signals to have active high polarity. The software can auto-detect and correct the polarity. The user should choose Automatic Mode to use this feature. Automatic Mode is the default mode. Otherwise, user can choose manual mode and provide the input polarities. The provided input polarities take effect only in manual mode. It will be used by hardware to correct the polarities. <br>"
    global Summary
    Summary.Command = "Write External Source Sync Polarity"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',180))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(IsManualPolarityDetection), 1, 0)
        value = setbits(int(IsVSyncActiveHigh), 1, 1)
        value = setbits(int(IsHSyncActiveHigh), 1, 2)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadExternalSourceSyncPolarity():
    "This command returns the input polarity detection mode for VSync and HSync signals for all external sources. For Automatic Mode it will return the polarities detected by the hardware as current VSync and HSync Polarity. For Manual Mode it will return the polarities provided by the user. <br>"
    global Summary
    Summary.Command = "Read External Source Sync Polarity"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',180))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        IsManualPolarityDetection = getbits(1, 0);
        IsVSyncActiveHigh = getbits(1, 1);
        IsHSyncActiveHigh = getbits(1, 2);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, IsManualPolarityDetection, IsVSyncActiveHigh, IsHSyncActiveHigh

def WriteFpdConfiguration(OperationMode,  Datamap,  PixelClockFrequencyRange):
    "This command configures the FPD receiver in the system to receive the external source over it's port(s). It will also start the system's external source detection process. This command should be used when the external source is given over FPDLink port. Internal sources get disabled so that the detection mechanisms are not affected by them. After sending this command, the host should check the source status using the Get Source Status Command to know whether an external source is detected successfully or not.<br> <br>The command will have no affect if the input parameters are the same as the current configuration of the system. Changing the Pixel format (RGB, YCbCr444, YCbCr422) will not restart the source detection process and will only configure the pixel format converters (loads the appropriate CSC matrix as well automatically). Source detection mechanism will restart for a change in any other parameter.<br> <br>This command is a Set Source Port Configuration command. <br>"
    global Summary
    Summary.Command = "Write Fpd Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',184))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',OperationMode.value)))
        writebytes.extend(list(struct.pack('B',Datamap.value)))
        writebytes.extend(list(struct.pack('B',PixelClockFrequencyRange.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadFpdConfiguration():
    "This command returns the current receiver configuration of the FPDLink receiver in the system. It will return Fail if FPDLink is not the currently active source. <br>"
    global Summary
    Summary.Command = "Read Fpd Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',184))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(3, writebytes, ProtocolData)
        OperationModeObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        DatamapObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        PixelClockFrequencyRangeObj = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, SrcFpdOperationModeT(OperationModeObj), SrcFpdDataMapT(DatamapObj), SrcFpdFRangeT(PixelClockFrequencyRangeObj)

def WriteFpdSwizzlerMap(FpdSwizzlerMap):
    "This command configures the for FPD source data lane mapping. <br>"
    global Summary
    Summary.Command = "Write Fpd Swizzler Map"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',185))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortaLaneZa.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortaLaneZb.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortaLaneZc.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortaLaneZd.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortaLaneZe.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortbLaneZa.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortbLaneZb.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortbLaneZc.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortbLaneZd.value)))
        writebytes.extend(list(struct.pack('B',FpdSwizzlerMap.SrcFpdPortbLaneZe.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadFpdSwizzlerMap():
    "This command is used to get the FPD source data lane mapping. <br>"
    global Summary
    Summary.Command = "Read Fpd Swizzler Map"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',185))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(10, writebytes, ProtocolData)
        FpdSwizzlerMap.SrcFpdPortaLaneZa = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        FpdSwizzlerMap.SrcFpdPortaLaneZb = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        FpdSwizzlerMap.SrcFpdPortaLaneZc = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        FpdSwizzlerMap.SrcFpdPortaLaneZd = struct.unpack_from ('B', bytearray(readbytes), 3)[0]
        FpdSwizzlerMap.SrcFpdPortaLaneZe = struct.unpack_from ('B', bytearray(readbytes), 4)[0]
        FpdSwizzlerMap.SrcFpdPortbLaneZa = struct.unpack_from ('B', bytearray(readbytes), 5)[0]
        FpdSwizzlerMap.SrcFpdPortbLaneZb = struct.unpack_from ('B', bytearray(readbytes), 6)[0]
        FpdSwizzlerMap.SrcFpdPortbLaneZc = struct.unpack_from ('B', bytearray(readbytes), 7)[0]
        FpdSwizzlerMap.SrcFpdPortbLaneZd = struct.unpack_from ('B', bytearray(readbytes), 8)[0]
        FpdSwizzlerMap.SrcFpdPortbLaneZe = struct.unpack_from ('B', bytearray(readbytes), 9)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, FpdSwizzlerMap

def WriteVboLaneConfiguration(NumLanes,  VboLaneConfiguration):
    "This command is used to set separate V-by-One swizzle setting based on lane configuration.<br> <br>The Set VBO Configuration command must follow this command for the lane swizzle to take place. The Set Execute Display command must follow the VBO commands for these settings to be updated. <br>"
    global Summary
    Summary.Command = "Write Vbo Lane Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',186))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',NumLanes.value)))
        writebytes.extend(list(struct.pack('B',VboLaneConfiguration.TxLane0.value)))
        writebytes.extend(list(struct.pack('B',VboLaneConfiguration.TxLane1.value)))
        writebytes.extend(list(struct.pack('B',VboLaneConfiguration.TxLane2.value)))
        writebytes.extend(list(struct.pack('B',VboLaneConfiguration.TxLane3.value)))
        writebytes.extend(list(struct.pack('B',VboLaneConfiguration.TxLane4.value)))
        writebytes.extend(list(struct.pack('B',VboLaneConfiguration.TxLane5.value)))
        writebytes.extend(list(struct.pack('B',VboLaneConfiguration.TxLane6.value)))
        writebytes.extend(list(struct.pack('B',VboLaneConfiguration.TxLane7.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadVboLaneConfiguration(NumLanes):
    "This command is used to get seperate V-by-One swizzle setting based on lane configuration. <br>"
    global Summary
    Summary.Command = "Read Vbo Lane Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',186))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',NumLanes.value)))
        readbytes = _readcommand(8, writebytes, ProtocolData)
        VboLaneConfiguration.TxLane0 = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        VboLaneConfiguration.TxLane1 = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        VboLaneConfiguration.TxLane2 = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        VboLaneConfiguration.TxLane3 = struct.unpack_from ('B', bytearray(readbytes), 3)[0]
        VboLaneConfiguration.TxLane4 = struct.unpack_from ('B', bytearray(readbytes), 4)[0]
        VboLaneConfiguration.TxLane5 = struct.unpack_from ('B', bytearray(readbytes), 5)[0]
        VboLaneConfiguration.TxLane6 = struct.unpack_from ('B', bytearray(readbytes), 6)[0]
        VboLaneConfiguration.TxLane7 = struct.unpack_from ('B', bytearray(readbytes), 7)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, VboLaneConfiguration

def WriteVboConfiguration(ByteMode,  DataMap,  DataRateFrequencyRange,  NumLanes):
    "This command configures the characteristics of the V-by-One (VBO) external video source.<br> <br>The byte mode is the color depth set by the front end.<br> <br>The data map is the color format that is transmitted from the video front end.<br> <br>The data rate frequency range is the bit rate window. If not defined by the front end, the bit rate window can be found by the following equation by multiplying the total pixel clock by the byte mode number multiplied by 10.<br> <br>The number of lanes is typically set by the video source. Note the source clock frequency, link clock frequency per lane, and the link transfer rate (or bit rate) per lane limitations when selecting a number of lanes. The source clock frequency is calculated by multiplying the total pixel clock by the number of bytes per pixel (byte mode) and dividing by the number of lanes. The link frequency per lane is the total pixel clock divided by the number of lanes. The link transfer rate per lane is the data rate frequency divided by the number of lanes.<br> <br>The minimum and maximum specifications for these parameters can be found in the V-by-One interface timing requirements section of the controller datasheet. The VBO configuration needs to be adjusted to meet the source frame timing requirements as well as the parameters mentioned above. The source frame timing requirements can also be found in the controller datasheet.<br> <br>The Horizontal Total of the video feed must be a multiple of 8.<br> <br><br>This command must be followed with a Write Execute Display command to be properly applied.<br> <br>"
    global Summary
    Summary.Command = "Write Vbo Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',187))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',ByteMode.value)))
        writebytes.extend(list(struct.pack('B',DataMap.value)))
        writebytes.extend(list(struct.pack('B',DataRateFrequencyRange.value)))
        writebytes.extend(list(struct.pack('B',NumLanes)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadVboConfiguration():
    "This command returns the characteristics of the VBO source. <br>"
    global Summary
    Summary.Command = "Read Vbo Configuration"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',187))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        ByteModeObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        DataMapObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        FrangeObj = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        NumLanes = struct.unpack_from ('B', bytearray(readbytes), 3)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, SrcVboByteModeT(ByteModeObj), SrcVboDataMapT(DataMapObj), SrcVboFRangeT(FrangeObj), NumLanes

def ReadVboStatus():
    "This command returns the status of the V-by-One source lock. <br>"
    global Summary
    Summary.Command = "Read Vbo Status"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',188))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        BitLocked = getbits(1, 0);
        DataLocked = getbits(1, 1);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, BitLocked, DataLocked

def ReadFrameCrc():
    "This command returns the CRC of the displayed image. <br>"
    global Summary
    Summary.Command = "Read Frame Crc"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',189))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        Crc = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Crc

def WriteVrrEnableQueued(VrrEnable):
    "This command is used to enable/disable VRR (Variable Refresh Rate). <br> It is a queued command, so must Set Execute Display after Enabling/Disabling. <br>"
    global Summary
    Summary.Command = "Write Vrr Enable Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',190))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(VrrEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadVrrEnableQueued():
    "This command returns if VRR (Variable Refresh Rate) is enabled or disabled. <br>"
    global Summary
    Summary.Command = "Read Vrr Enable Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',190))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        VrrEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, VrrEnable

def WriteSplashScreenSelect(Index):
    "This command specifies which splash screen is to be displayed among the splash screen images stored in the firmware image. <br> <br>The splash screen is read over the flash interface and sent down the controller image processing path once and then stored in the frame buffer. As such, all image processing settings (e.g. image crop, image orientation, display size, splash screen reference number) should be set by the user.<br> <br>The availability of splash screens is limited by the available space in flash memory, and all splash screens must use landscape orientation.<br> <br>The minimum splash image size allowed for flash storage is 640 in horizontal resolution and 360 in vertical resolution. The maximum size supported matches the full display resolution available on the DMD, and splash screens are typically set to the full resolution. Full resolution is useful for supporting optical test splash screens.<br> <br>The user must specify how the splash image is displayed on the screen. Key commands for this are Set Image Crop and Set Display Size.<br> <br>When issued to the controller this command makes splash screen as the active source being displayed. The controller then stores the specified splash screen reference number, and the controller software also reads the header information from flash for this splash screen and stores this in internal memory.  <br> <br>This command must be followed with a Write Execute Display command. <br><br>"
    global Summary
    Summary.Command = "Write Splash Screen Select"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',193))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Index)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadSplashScreenSelect():
    "This command returns the splash image index. <br>"
    global Summary
    Summary.Command = "Read Splash Screen Select"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',193))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        Index = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Index

def ReadSplashScreenHeader(Index):
    "This command returns splash image header info from the index. If there is no splash screen stored in the frame buffer for the selection given by command Set Splash Screen, this is considered an error. The command Get Communication Errors will return invalid command parameter error. <br>"
    global Summary
    Summary.Command = "Read Splash Screen Header"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',194))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Index)))
        readbytes = _readcommand(6, writebytes, ProtocolData)
        HorzResolution = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        VertResolution = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        PixelFormatObj = struct.unpack_from ('B', bytearray(readbytes), 4)[0]
        CompressionTypeObj = struct.unpack_from ('B', bytearray(readbytes), 5)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, HorzResolution, VertResolution, SplashPixelFormatT(PixelFormatObj), SplashCompressionT(CompressionTypeObj)

def ReadControllerId():
    "This command returns the device ID for the controller(s). <br>"
    global Summary
    Summary.Command = "Read Controller Id"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',64))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(16, writebytes, ProtocolData)
        FirstControllerDeviceId = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
        SecondControllerDeviceId = struct.unpack_from ('I', bytearray(readbytes), 4)[0]
        ThirdControllerDeviceId = struct.unpack_from ('I', bytearray(readbytes), 8)[0]
        ForthControllerDeviceId = struct.unpack_from ('I', bytearray(readbytes), 12)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, FirstControllerDeviceId, SecondControllerDeviceId, ThirdControllerDeviceId, ForthControllerDeviceId

def ReadDmdId():
    "This command returns the device ID and fuse ID for the DMD. <br>"
    global Summary
    Summary.Command = "Read Dmd Id"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',65))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(16, writebytes, ProtocolData)
        DmdDeviceId = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
        DmdFuseId = struct.unpack_from ('I', bytearray(readbytes), 4)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DmdDeviceId, DmdFuseId

def ReadPmicId():
    "This command returns the device ID for the PMIC. <br>"
    global Summary
    Summary.Command = "Read Pmic Id"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',66))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        PmicDeviceId = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, PmicDeviceId

def ReadDmdTrainingResults(Channel,  Pin):
    "This command returns the DMD Training results. <br>"
    global Summary
    Summary.Command = "Read Dmd Training Results"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',67))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Channel)))
        writebytes.extend(list(struct.pack('B',Pin)))
        readbytes = _readcommand(16, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        DmdTrainingResults.IsChannelActive = getbits(1, 0);
        readdata = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        packerinit(readdata)
        DmdTrainingResults.IsPinActive = getbits(1, 0);
        readdata = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        packerinit(readdata)
        DmdTrainingResults.LastKnownGoodDll = getbits(1, 0);
        DmdTrainingResults.BitResult6332 = struct.unpack_from ('I', bytearray(readbytes), 3)[0]
        DmdTrainingResults.BitResult3100 = struct.unpack_from ('I', bytearray(readbytes), 7)[0]
        DmdTrainingResults.HighPass = struct.unpack_from ('B', bytearray(readbytes), 11)[0]
        DmdTrainingResults.LowPass = struct.unpack_from ('B', bytearray(readbytes), 12)[0]
        DmdTrainingResults.DllDelay = struct.unpack_from ('B', bytearray(readbytes), 13)[0]
        DmdTrainingResults.Error = struct.unpack_from ('H', bytearray(readbytes), 14)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DmdTrainingResults

def WriteDmdTrueGlobalReset(GlobalResetEnable):
    "This command sets the display mode to true global. The True Global mode should be set to true only during factory/assembly operation and is primarily designed for DMD protection on systems being tested or assembled at the cost of improved image quality.<br> <br>Note that true global mode will not take place until the system is rebooted. This means that the system must contain an EEPROM that can store the true global mode setting. After we store the DmdTrueGlobalReset bit to EEPROM we probe a hard reset. <br>"
    global Summary
    Summary.Command = "Write Dmd True Global Reset"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',68))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(GlobalResetEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDmdTrueGlobalReset():
    "This command returns whether or not true global mode is enabled."
    global Summary
    Summary.Command = "Read Dmd True Global Reset"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',68))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        GlobalResetEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, GlobalResetEnable

def ReadSystemErrors():
    "This command returns the overall system errors."
    global Summary
    Summary.Command = "Read System Errors"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',69))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        SystemErrors.DmdProjectMismatchError = getbits(1, 0);
        SystemErrors.DmdInitializationError = getbits(1, 1);
        SystemErrors.DmdLsifError = getbits(1, 2);
        SystemErrors.DmdHsifError = getbits(1, 3);
        SystemErrors.DmdTrainingError = getbits(1, 4);
        SystemErrors.DmdPowerDownError = getbits(1, 5);
        SystemErrors.DmdPreconditioningError = getbits(1, 6);
        SystemErrors.DmdParkError = getbits(1, 7);
        readdata = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        packerinit(readdata)
        SystemErrors.ProductConfigurationFailed = getbits(1, 0);
        SystemErrors.DlpcInitializationError = getbits(1, 1);
        SystemErrors.SequencerError = getbits(1, 2);
        SystemErrors.SequenceSelectionFailed = getbits(1, 3);
        SystemErrors.TemperatureOvershoot = getbits(1, 4);
        SystemErrors.SequenceStalled = getbits(1, 5);
        SystemErrors.DisplayExecutionOnPowerupFailed = getbits(1, 6);
        readdata = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        packerinit(readdata)
        SystemErrors.EepromInitializationError = getbits(1, 0);
        SystemErrors.DlpaCommError = getbits(1, 1);
        SystemErrors.LedFault = getbits(1, 2);
        SystemErrors.DutyCycleUpdateError = getbits(1, 3);
        SystemErrors.GpioConflictError = getbits(1, 4);
        readdata = struct.unpack_from ('B', bytearray(readbytes), 3)[0]
        packerinit(readdata)
        SystemErrors.UartPort0CommError = getbits(1, 0);
        SystemErrors.SspPort0CommError = getbits(1, 1);
        SystemErrors.SspPort1CommError = getbits(1, 2);
        SystemErrors.I2CPort0CommError = getbits(1, 3);
        SystemErrors.I2CPort1CommError = getbits(1, 4);
        SystemErrors.UsbPortCommError = getbits(1, 5);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, SystemErrors

def ReadSystemStatus():
    "This command reads the overall system status from the controller."
    global Summary
    Summary.Command = "Read System Status"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',70))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(3, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        SystemStatus.SystemInitializationDone = getbits(1, 0);
        SystemStatus.SystemError = getbits(1, 1);
        SystemStatus.VideoPortError = getbits(1, 2);
        SystemStatus.DisplayResetAtPowerup = getbits(1, 3);
        readdata = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        packerinit(readdata)
        SystemStatus.ActuatorCalibrationMode = getbits(1, 0);
        readdata = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        packerinit(readdata)
        SystemStatus.SequencePhaselock = getbits(1, 0);
        SystemStatus.SequenceFrequencylock = getbits(1, 1);
        SystemStatus.RedLedEnabled = getbits(1, 2);
        SystemStatus.GreenLedEnabled = getbits(1, 3);
        SystemStatus.BlueLedEnabled = getbits(1, 4);
        SystemStatus.ColorWheelSpinning = getbits(1, 5);
        SystemStatus.ColorWheelPhaseLock = getbits(1, 6);
        SystemStatus.ColorWheelFrequencyLock = getbits(1, 7);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, SystemStatus

def ReadSystemRunningMode():
    "This command returns the current running mode of the system. Some of the modes are for future use only and may not be available to use. <br>"
    global Summary
    Summary.Command = "Read System Running Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',71))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        SystemRunningModeObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DdpSystemModeT(SystemRunningModeObj)

def ReadFlashVersion():
    "This command reads the version number that uniquely identifies the flash image. <br>"
    global Summary
    Summary.Command = "Read Flash Version"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',72))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(3, writebytes, ProtocolData)
        FlashVersionMajor = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        FlashVersionMinor = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        FlashVersionSubminor = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, FlashVersionMajor, FlashVersionMinor, FlashVersionSubminor

def ReadSystemTemperature():
    "This command is used to read the system temperature using an external thermistor via the DLPA (if available). <br>"
    global Summary
    Summary.Command = "Read System Temperature"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',74))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        SystemTemprature = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, SystemTemprature

def ReadLastCommandResult():
    "This command returns the execution result of the last command. <br>"
    global Summary
    Summary.Command = "Read Last Command Result"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',77))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(5, writebytes, ProtocolData)
        Destination = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        CommandId = struct.unpack_from ('H', bytearray(readbytes), 1)[0]
        ErrorCodeObj = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Destination, CommandId, ErrCodeT(ErrorCodeObj)

def ReadDlpaMainStatus():
    "This command gets main status of DLPA. <br>"
    global Summary
    Summary.Command = "Read Dlpa Main Status"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',78))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        DlpaMainStatus.TsWarn = getbits(1, 0);
        DlpaMainStatus.TsShut = getbits(1, 1);
        DlpaMainStatus.BatLowWarn = getbits(1, 2);
        DlpaMainStatus.BatLowShut = getbits(1, 3);
        DlpaMainStatus.DmdFault = getbits(1, 4);
        DlpaMainStatus.ProjOnInt = getbits(1, 5);
        DlpaMainStatus.IllumFault = getbits(1, 6);
        DlpaMainStatus.SupplyFault = getbits(1, 7);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DlpaMainStatus

def ReadProductConfigHash():
    "This command returns product configuration hash. <br>"
    global Summary
    Summary.Command = "Read Product Config Hash"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',79))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        Hash = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Hash

def WriteDmdMirrorLock(MirrorLockEnable):
    "This command enable/disable Mirror Lock Mode. The Mirror Protection mode should be set to DMD_MIRROR_LOCK and this mode should be used only during factory/assembly operation and is primarily designed for DMD protection on systems being tested or assembled at the cost of improved image quality.<br> <br>Note that Mirror Lock mode will take place immediately upon receiving this command. <br>"
    global Summary
    Summary.Command = "Write Dmd Mirror Lock"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',82))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(MirrorLockEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDmdMirrorLock():
    "This command returns whether or not Mirror Lock mode is enabled."
    global Summary
    Summary.Command = "Read Dmd Mirror Lock"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',82))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        MirrorLockEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, MirrorLockEnable

def WriteFirmwareUpdateMode(Enable):
    "<br>This command switches the system to prepare for firmware update mode with display kept on. The front-end can setup the datapath to display a source of their choice before entering this mode. This mode can be entered only if last executed display operation was successful, and no pending/queued commands are present. Only native display resolution of the product is supported in this mode. <br>Once this mode is entered, only commands related to updating firmware will be available for execution. Once this command is sent, the system will wait for all background tasks to settle before allowing firmware update. Depending on the state of the system when this command was issued, system may switch to a 'Prepare for Firmware update' mode instead of 'Firmware update mode'. The application processor should poll on 'Read System Running Mode' command to ensure the system entered the 'Firmware update mode'. Only upon entering 'Firmware update mode', the flash update commands will be available to send to the DLP Controller. <br>Once the update is complete, use this command to exit the firmware update mode. When exiting the mode, the command will automatically do basic validation to ensure system can successfully boot with the updated firmware image. A system restart is automatically triggered upon successful verification. <br>TI recommends the application processor to follow a specific order of operation while they execute a firmware over the air update. See additional documentation made available from TI. Deviating from this flow can cause recovery challenging in case of a power disruption during firmware update. <br>"
    global Summary
    Summary.Command = "Write Firmware Update Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',85))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(Enable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WritePreventMainappSwitch():
    "This command when set prevents the system from entering mainapp on bootup <br>"
    global Summary
    Summary.Command = "Write Prevent Mainapp Switch"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',86))
        ProtocolData.OpcodeLength = 1;
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadFlashBlocksSizeAndOffset(FlashBlock):
    "This command returns the desired flash block size and offset. <br>"
    global Summary
    Summary.Command = "Read Flash Blocks Size And Offset"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',195))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',FlashBlock.value)))
        readbytes = _readcommand(8, writebytes, ProtocolData)
        Size = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
        StartAddress = struct.unpack_from ('I', bytearray(readbytes), 4)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Size, StartAddress

def ReadSchemaVersion(Type):
    "This command returns the Calibration/User Settings Schema Version <br>Note: If type is OEM Scratch pad it errors out. <br>"
    global Summary
    Summary.Command = "Read Schema Version"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',196))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Type.value)))
        readbytes = _readcommand(4, writebytes, ProtocolData)
        Version = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Version

def WriteTpgPreDefinedTimingsQueued(Index):
    "This command selects a pre-defined TPG timing that is stored in flash. This command will validate and set the frame rate, active resolution, and blankings.<br> <br>This command must be followed with a Write Execute Display command to be applied. <br>"
    global Summary
    Summary.Command = "Write Tpg Pre Defined Timings Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',160))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Index)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgPreDefinedTimingsQueued():
    "This command selects a pre-defined TPG timing that is stored in flash. This command will validate and set the frame rate, active resolution, and blankings. <br>"
    global Summary
    Summary.Command = "Read Tpg Pre Defined Timings Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',160))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        Index = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Index

def WriteTpgFrameRate(FrameRate):
    "This command specifies the frame rate to be used when a test pattern generator (TPG) image is displayed. <br>"
    global Summary
    Summary.Command = "Write Tpg Frame Rate"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',161))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',FrameRate)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgFrameRate():
    "This command returns frame rate in Hz for current test pattern. <br>"
    global Summary
    Summary.Command = "Read Tpg Frame Rate"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',161))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        FrameRate = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, FrameRate

def WriteTpgPreDefinedPattern(Index):
    "This command will set one of the pre-defined test patterns stored in flash. The function selects a pattern to load from flash into the test pattern generator hardware. The information retrieved from the flash includes pattern definition, color definition, and the resolution. The Set Execute Display command must be called to switch the display mode from other modes to TPG prior to or after this command. <br>"
    global Summary
    Summary.Command = "Write Tpg Pre Defined Pattern"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',162))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',Index)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgPreDefinedPattern():
    "This command returns the current selection for pre-defined test patterns. <br>"
    global Summary
    Summary.Command = "Read Tpg Pre Defined Pattern"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',162))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(2, writebytes, ProtocolData)
        Index = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Index

def WriteTpgBorder(BorderWidth):
    "This command enables a white border around the test pattern of given width. This is applicable only when TPG is selected as display source. <br>"
    global Summary
    Summary.Command = "Write Tpg Border"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',163))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',BorderWidth)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgBorder():
    "The commands returns the TPG border width in number of pixels. <br>"
    global Summary
    Summary.Command = "Read Tpg Border"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',163))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        BorderWidth = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, BorderWidth

def WriteTpgSolidField(Red,  Green,  Blue):
    "This command sets color for solid field test pattern by selecting the intensity of each primary color. <br>"
    global Summary
    Summary.Command = "Write Tpg Solid Field"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',164))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',Red)))
        writebytes.extend(list(struct.pack('H',Green)))
        writebytes.extend(list(struct.pack('H',Blue)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgSolidField():
    "This command returns color for current solid field set by test patter generator. If Solid Field is not enabled via TPG, an error will be returned. <br>"
    global Summary
    Summary.Command = "Read Tpg Solid Field"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',164))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(6, writebytes, ProtocolData)
        Red = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        Green = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        Blue = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Red, Green, Blue

def WriteKeystoneEnableQueued(KeystoneEnable):
    "This command sets Keystone By Angles and Corners feature. <br><br>"
    global Summary
    Summary.Command = "Write Keystone Enable Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',97))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(KeystoneEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadKeystoneEnableQueued():
    "This command provides status of Keystone By Angles and Corners feature. <br>"
    global Summary
    Summary.Command = "Read Keystone Enable Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',97))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        KeystoneEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, KeystoneEnable

def WriteOpticalParametersQueued(ThrowRatio,  VerticalOffset):
    "This command configures the optical parameters for the keystone correction when the throw ratio & the vertical offset for the projector are known.<br> <br>To adjust images to compensate for pitch and yaw movements of the projector, 1D/2D keystone correction and warping must know the projector鈥檚 optical throw ratio and optical vertical offset. <br>"
    global Summary
    Summary.Command = "Write Optical Parameters Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',98))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(ThrowRatio,256)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(VerticalOffset,256)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadOpticalParametersQueued():
    "This command returns the optical parameters currently set. <br>"
    global Summary
    Summary.Command = "Read Optical Parameters Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',98))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(4, writebytes, ProtocolData)
        ThrowRatio = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 0)[0], 256)
        VerticalOffset = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 2)[0], 256)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ThrowRatio, VerticalOffset

def WriteKeystoneAnglesQueued(Pitch,  Yaw,  Roll):
    "<br>This command configures the Keystone correction when the pitch, yaw, and roll for the corrected image are known. Keystone correction is used to remove the distortion caused when the projector is not orthogonal to the projection surface (screen). Roll correction is used to remove the distortion caused when the projector is rotated while projecting an image. 3D keystone correction is used to remove the distortion when the projector is both rotated and not orthogonal to the projection surface. <br>This command provides pitch angle and yaw angle inputs as needed for the controller to perform 1D or 2D keystone correction. This command provides a roll angle input as needed for the controller to perform roll correction. If pitch angle and yaw angle are also input, then 3D keystone correction is performed. <br>For the projector鈥檚 pitch, yaw and roll angles to be properly comprehended by the controller software, the projector鈥檚 optical throw ratio and optical vertical offset must be entered using command Set Optical Parameters. <br>The keystone correction feature is enabled when command Set Warp Feature Control settings are selected and enabled. <br>"
    global Summary
    Summary.Command = "Write Keystone Angles Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',99))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(Pitch,256)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(Yaw,256)))))
        writebytes.extend(list(struct.pack('H',int(convertfloattofixed(Roll,256)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadKeystoneAnglesQueued():
    "This command returns the keystone configuration parameters currently set. <br>"
    global Summary
    Summary.Command = "Read Keystone Angles Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',99))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(6, writebytes, ProtocolData)
        Pitch = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 0)[0], 256)
        Yaw = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 2)[0], 256)
        Roll = convertfixedtofloat(struct.unpack_from ('H', bytearray(readbytes), 4)[0], 256)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Pitch, Yaw, Roll

def WriteKeystoneCornersQueued(KeystoneCornersQueued):
    "This command configures the 2D keystone correction when the corners of the corrected image are known. Keystone correction is used to remove the distortion caused when the projector is not orthogonal to the projection surface (screen). For the effects to take place, the Keystone feature has to be enabled. <br>"
    global Summary
    Summary.Command = "Write Keystone Corners Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',100))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',KeystoneCornersQueued.TopLeftX)))
        writebytes.extend(list(struct.pack('H',KeystoneCornersQueued.TopLeftY)))
        writebytes.extend(list(struct.pack('H',KeystoneCornersQueued.TopRightX)))
        writebytes.extend(list(struct.pack('H',KeystoneCornersQueued.TopRightY)))
        writebytes.extend(list(struct.pack('H',KeystoneCornersQueued.BottomLeftX)))
        writebytes.extend(list(struct.pack('H',KeystoneCornersQueued.BottomLeftY)))
        writebytes.extend(list(struct.pack('H',KeystoneCornersQueued.BottomRightX)))
        writebytes.extend(list(struct.pack('H',KeystoneCornersQueued.BottomRightY)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadKeystoneCornersQueued():
    "This command returns the keystone configuration parameters currently set. <br>"
    global Summary
    Summary.Command = "Read Keystone Corners Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',100))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(16, writebytes, ProtocolData)
        KeystoneCornersQueued.TopLeftX = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        KeystoneCornersQueued.TopLeftY = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        KeystoneCornersQueued.TopRightX = struct.unpack_from ('H', bytearray(readbytes), 4)[0]
        KeystoneCornersQueued.TopRightY = struct.unpack_from ('H', bytearray(readbytes), 6)[0]
        KeystoneCornersQueued.BottomLeftX = struct.unpack_from ('H', bytearray(readbytes), 8)[0]
        KeystoneCornersQueued.BottomLeftY = struct.unpack_from ('H', bytearray(readbytes), 10)[0]
        KeystoneCornersQueued.BottomRightX = struct.unpack_from ('H', bytearray(readbytes), 12)[0]
        KeystoneCornersQueued.BottomRightY = struct.unpack_from ('H', bytearray(readbytes), 14)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, KeystoneCornersQueued

def WriteManualWarpEnableQueued(ManualWarpEnable):
    "This command sets Manual Warp feature. <br><br>"
    global Summary
    Summary.Command = "Write Manual Warp Enable Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',101))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(ManualWarpEnable), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadManualWarpEnableQueued():
    "This command provides status of Manual Warp feature. <br>"
    global Summary
    Summary.Command = "Read Manual Warp Enable Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',101))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        ManualWarpEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, ManualWarpEnable

def WriteManualWarpControlPointsQueued(ControlPointsDefinedByArray,  HorizontalCtrlPoints,  VerticalCtrlPoints):
    "This command sets up the user defined control points of the warp map if warping feature is enabled. <br>The warping map table loaded by the manual warp table write command is used as a two dimensional array with dimension which is defined based on the first argument of this command: - TRUE  = (NumHorzCtrlPoints x NumVertCtrlPoints) - FALSE = (32 x 18) values <br>The points in the map should lie within the display area defined by display image size command. Any points lying outside the display area shall get cropped. <br><br>"
    global Summary
    Summary.Command = "Write Manual Warp Control Points Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',102))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',ControlPointsDefinedByArray.value)))
        pass  # Invalid ArrayType placeholder fixed
        pass  # Invalid ArrayType placeholder fixed
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadManualWarpControlPointsQueued():
    "This command returns the user defined warping map control points. <br>"
    global Summary
    Summary.Command = "Read Manual Warp Control Points Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',102))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        ControlPointsDefinedByArrayObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        pass  # Invalid ArrayType placeholder fixed
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, WrpMwCpTypeT(ControlPointsDefinedByArrayObj), CtrlPoints

def WriteManualWarpTableQueued(WarpTableIndex,  WarpPoints):
    "This command writes to the warp map table that can be enabled using the enable Manual Warping Command. N warp map points (that does not exceed the command packet size) can be loaded at a time to anywhere within the table. Maximum number of points that can be set using this command is 32 in the horizontal direction and 18 in the vertical direction. Overall max 576 points. The number of points set by this command should match the number of control points specified using Manual Warp Control Points command. <br>The warp map table is stored in a RAM inside the controller.This command writes the entire warp map table or any contiguous subset of points within the warp map table. <br>"
    global Summary
    Summary.Command = "Write Manual Warp Table Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',103))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',WarpTableIndex)))
        pass  # Invalid ArrayType placeholder fixed
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadManualWarpTableQueued(WarpTableIndex,  NumberOfEntries):
    "This command reads back already applied warp map table. N warp map points (that does not exceed the command packet size) can be read at a time from anywhere within the table. Maximum table size is 1952. <br>"
    global Summary
    Summary.Command = "Read Manual Warp Table Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',103))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',WarpTableIndex)))
        writebytes.extend(list(struct.pack('H',NumberOfEntries)))
        readbytes = _readcommand(0, writebytes, ProtocolData)
        pass  # Invalid ArrayType placeholder fixed
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, WarpPoints

def WriteApplyWarpMapFromIndexQueued(Index):
    "This command sets Manual Warp feature. <br><br>"
    global Summary
    Summary.Command = "Write Apply Warp Map From Index Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',104))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Index)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteRefactorMap(ReSamplePointsX,  ReSamplePointsY):
    "This command can be used refractor input warp map to less/more number of control points and warp points and no need of set execute display When you read control points and warp points you can get re-factored Control points and Warp points Ex: User has provided 3*3 Warp map and does set execute display and now user want to refactor to 5*3 then apply 5*5 using this command and read back, user will get refactored Warp map <br>"
    global Summary
    Summary.Command = "Write Refactor Map"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',105))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('H',ReSamplePointsX)))
        writebytes.extend(list(struct.pack('H',ReSamplePointsY)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadWarpStatus():
    "This command returns general warping status <br>"
    global Summary
    Summary.Command = "Read Warp Status"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',109))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        SelfCorrectionEnable = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, SelfCorrectionEnable

def WriteLeftmostPixelQueued(LeftMostPixel):
    "This command sets if left most pixel is availble in system or not. <br>Left most pixel setting is only required for diamond DMDs and 2 way manhattan XPR. User need to follow calibration guide to decide if Left most pixel is present or not in their system and set this value as per that. <br><br>This command must be followed with a Write Execute Display command to be applied.<br> <br>"
    global Summary
    Summary.Command = "Write Leftmost Pixel Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',127))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(LeftMostPixel), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadLeftmostPixelQueued():
    "This command returns if Left most pixel is present in system. <br>"
    global Summary
    Summary.Command = "Read Leftmost Pixel Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',127))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        LeftMostPixel = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, LeftMostPixel

def WriteXprEnableModeQueued(Mode):
    "This command sets the XPR mode. <br> In XPR On the actuator drivers are always engaged. In XPR Off the actuator drivers are always disabled. In XPR Auto the system determines if the actuator drives should be driven.<br> <br>An XPR waveform will not be seen when the controller is configured for a 1080p using frame rates exceeding 62Hz.<br> <br>Note that a fixed output of 1.65V is expected in the case that XPR is enabled and an unstable FSync or invalid configuration is detected. <br><br>This command must be followed with a Write Execute Display command to be applied.<br> <br>"
    global Summary
    Summary.Command = "Write Xpr Enable Mode Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',128))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',Mode.value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadXprEnableModeQueued():
    "This command returns the current XPR Enable Mode. <br>"
    global Summary
    Summary.Command = "Read Xpr Enable Mode Queued"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',128))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        ModeObj = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DispXprEnableModeT(ModeObj)

def WriteXprCalibrationMode():
    "This command enables an image processing bypass mode for use during XPR calibration. <br> This command causes the controller to bypass all image processing including XPR image processing and establishes a one-to-one correspondence between source image pixels and the mirrors on the DMD. This mode is useful for seeing clear splits between XPR subframes when performing XPR calibration. XPR calibration is needed to assure the mechanical actuator has optimal alignment when the system displays each spatially-shifted subframe image.<br> <br>This command must be followed with a Write Execute Display command to be applied, along with speacial calibration Splash or external image set. <br>There is no readback command for this setting because there is no exit from this bypass mode. To exit bypass a system restart is required. <br>"
    global Summary
    Summary.Command = "Write Xpr Calibration Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',129))
        ProtocolData.OpcodeLength = 1;
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteXprActuatorPosition(PositionNumber):
    "This command sets the position of the XPR mechanical actuator for calibration purposes. There are 24 possible mechanical positions for 4-way actuator. Use this command while performing XPR calibration using a TI-provided XPR calibration splash image. <br> <br>For this command to take effect, command Set XPR Calibration Mode must be enabled. <br>"
    global Summary
    Summary.Command = "Write Xpr Actuator Position"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',130))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',PositionNumber)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadXprActuatorPosition():
    "This command sets the position of the XPR mechanical actuator for calibration purposes."
    global Summary
    Summary.Command = "Read Xpr Actuator Position"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',130))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        PositionNumber = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, PositionNumber

def WriteXprActuatorDacGain(AwcChannel,  Gain):
    "<br>This command configures the DAC gain for actuator waveforms 0 and 1. <br><br>This command must be followed with a Write Execute Display command to be applied.<br> <br>"
    global Summary
    Summary.Command = "Write Xpr Actuator Dac Gain"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',131))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        writebytes.extend(list(struct.pack('B',int(convertfloattofixed(Gain,128)))))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadXprActuatorDacGain(AwcChannel):
    "This command configures the DAC gain for actuator waveforms 0 and 1. <br>"
    global Summary
    Summary.Command = "Read Xpr Actuator Dac Gain"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',131))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        readbytes = _readcommand(1, writebytes, ProtocolData)
        Gain = convertfixedtofloat(struct.unpack_from ('B', bytearray(readbytes), 0)[0], 128)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Gain

def WriteXprActuatorSubframeDelay(AwcChannel,  Delay):
    "<br>This command configures the subframe delay for actuator waveforms 0 and 1. <br><br>This command must be followed with a Write Execute Display command to be applied.<br> <br>"
    global Summary
    Summary.Command = "Write Xpr Actuator Subframe Delay"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',132))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        writebytes.extend(list(struct.pack('I',Delay)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadXprActuatorSubframeDelay(AwcChannel):
    "This command configures the subframe delay for actuator waveforms 0 and 1. <br>"
    global Summary
    Summary.Command = "Read Xpr Actuator Subframe Delay"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',132))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        readbytes = _readcommand(4, writebytes, ProtocolData)
        Delay = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Delay

def WriteXprActuatorDacOffset(AwcChannel,  Offset):
    "<br>This command configures the subframe delay for actuator waveforms 0 and 1. <br><br>This command must be followed with a Write Execute Display command to be applied.<br> <br>"
    global Summary
    Summary.Command = "Write Xpr Actuator Dac Offset"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',133))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        writebytes.extend(list(struct.pack('b',Offset)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadXprActuatorDacOffset(AwcChannel):
    "This command configures the subframe delay for actuator waveforms 0 and 1. <br>"
    global Summary
    Summary.Command = "Read Xpr Actuator Dac Offset"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',133))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        readbytes = _readcommand(1, writebytes, ProtocolData)
        Offset = struct.unpack_from ('b', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Offset

def WriteXprActuatorFixedOutputLevel(AwcChannel,  Level):
    "<br>This command configures the fixed output level for actuator waveforms 0 and 1.<br> <br>Note that a fixed output of 1.65V is expected in the case that XPR is enabled and an unstable FSync or invalid configuration is detected. If XPR is disabled, or a 1080p resolution is configured for boot up, the output is expected to be at 0V. <br><br>This command must be followed with a Write Execute Display command to be applied.<br> <br>"
    global Summary
    Summary.Command = "Write Xpr Actuator Fixed Output Level"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',134))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        writebytes.extend(list(struct.pack('b',Level)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadXprActuatorFixedOutputLevel(AwcChannel):
    "This command configures the fixed output level for actuator waveforms 0 and 1. <br>"
    global Summary
    Summary.Command = "Read Xpr Actuator Fixed Output Level"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',134))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        readbytes = _readcommand(1, writebytes, ProtocolData)
        Level = struct.unpack_from ('b', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Level

def WriteDisplayConfigMode(DisplayBlack):
    "<br>This command is used to set whether display black needs to be used to hide transitional artifact durig display re-config. <br>"
    global Summary
    Summary.Command = "Write Display Config Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 4;
    try:
        writebytes=list(struct.pack('B',166))
        ProtocolData.OpcodeLength = 1;
        packerinit()
        value = setbits(int(DisplayBlack), 1, 0)
        writebytes.extend(list(struct.pack('B',value)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadDisplayConfigMode():
    "Data returned is in the same format as Write Parameters for command Set Display Config Mode. <br>"
    global Summary
    Summary.Command = "Read Display Config Mode"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 4;
    try:
        writebytes=list(struct.pack('B',166))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(1, writebytes, ProtocolData)
        readdata = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        packerinit(readdata)
        DisplayBlack = getbits(1, 0);
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, DisplayBlack

def ReadFlashLayoutVersion():
    "This command returns supported layout revision numbers and hash for flash config and app config layout. <br>"
    global Summary
    Summary.Command = "Read Flash Layout Version"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 4;
    try:
        writebytes=list(struct.pack('B',0))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(68, writebytes, ProtocolData)
        FlashCfgLayoutVersion = struct.unpack_from ('H', bytearray(readbytes), 0)[0]
        FlashCfgLayoutHash = str(bytearray(readbytes), encoding)
        AppCfgLayoutVersion = struct.unpack_from ('H', bytearray(readbytes), 2)[0]
        AppCfgLayoutHash = str(bytearray(readbytes), encoding)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, FlashCfgLayoutVersion, FlashCfgLayoutHash, AppCfgLayoutVersion, AppCfgLayoutHash

def ReadComposerVersion():
    "This command returns the Composer Version with which the flash image has been built. <br>"
    global Summary
    Summary.Command = "Read Composer Version"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 4;
    try:
        writebytes=list(struct.pack('B',1))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(12, writebytes, ProtocolData)
        Major = struct.unpack_from ('B', bytearray(readbytes), 0)[0]
        Minor1 = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        Minor2 = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        Patch = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
        BuildHash = str(bytearray(readbytes), encoding)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Major, Minor1, Minor2, Patch, BuildHash

def WriteXprActuatorWaveformControlParameter(XprCommand,  AwcChannel,  Data):
    "<br>This command configures the Actuator Waveform Control(AWC) block. Here, AWCx can be AWC 0 or 1. Bytes 2-5 contains the XPR command data as mentioned in Byte 0. Byte 1 contains AWC channel number, possible values are 0 or 1.<br> <br>Fixed Output Enable : Configures Actuator in fixed output mode.<BR> Byte    2: 0x00 - Disable 0x01 - Enable  <BR> Bytes 3-5: Reserved must be set to 0x000000<br> <br>Gain : Set Waveform Generator DAC/PWM Gain.<BR> Byte    2: Range 0 - 255 format u1.7 (0 to 1.9921875) <BR> Bytes 3-5: Reserved must be set to 0x000000<BR><BR> <br>Subframe delay : Subframe delay Bytes 2-5; Range 0 - 262143 and lsb = 133.333ns  <BR><BR> <br>Actuator Type (READ ONLY) : Actuator type <BR> Byte    2: <BR>0x00 - NONE <BR> 0x01 - Optotune (XPR-25 Model) <BR> 0x80 - TI Actuator Interface (EEPROM) <BR> 0x81 - TI Actuator Interface (MCU) <BR> Bytes 3-5: Reserved must be set to 0x000000<BR><BR> <br>Output Enable/Disable : Actuator output enable/disable <BR> Byte    2: 0x00 - Disable 0x01 - Enable  <BR> Bytes 3-5: Reserved must be set to 0x000000<br> Note: Both AWC0 and AWC1 disabled/enabled together <BR> <br>Clock Width : Defines the high and low width for the output clock (the clock period will be 2*(ClkWidth+1)) <BR> 0 = 1 (Clock period is two clocks); lsb = 8.33ns <BR> Bytes 2-5 : ClkWidth <BR> Example: ClkWidth = 0; will generate clock of 2*(0+1)*8.33 = 16.66ns <BR><BR> <br>Offset : DAC/PWM Output Offset <BR> Byte    2: Range -128 - +127 format S7 (-128 to +127) <BR> Bytes 3-5: Reserved must be set to 0x000000<BR><BR> <br>Number of Segments : Defines number of segments <BR> Byte    2: Range 2 - 255<BR> Bytes 3-5: Reserved must be set to 0x000000<BR><BR> <br>Segments Length : Defines size of the segments <BR> Bytes 2-3: Range 19 - 4095<BR> Bytes 4-5: Reserved must be set to 0x0000<BR><BR> <br>Invert PWM A : Applicable when AWC is configured to PWM type instead of DAC <BR> Byte    2: 0x00 - No inversion <BR> 0x01 - Inverted  <BR> Bytes 3-5: Reserved must be set to 0x000000<BR><BR> <br>Invert PWM B : Applicable when AWC is configured to PWM type instead of DAC <BR> Byte    2: 0x00 - No inversion 0x01 - Inverted  <BR> Bytes 3-5: Reserved must be set to 0x000000<BR><BR> <br>Subframe Filter Value : Sets Subframe Filter Value - defines the minimum time between Subframe edges. Edges closer than the set value will be filtered out <BR> Byte    2: 0 = Filter disabled, >0 = Filter time will be Val x 60us, Range: 0 - 255 <BR> Bytes 3-5: Reserved must be set to 0x000000<BR><BR> <br>Subframe Watch Dog : Defines the maximum time between Subframe edges; if timer expires, then the WG will automatically output the Fixed Output value, and the normal output will resume on the next subframe edge.<BR> Bytes 2-3: 0 = Subframe watchdog disabled, >0 = Watchdog time will be Time x 60us, Range: Range: 0 - 1023 <BR> Bytes 4-5: Reserved must be set to 0x0000<BR><BR> <br>Fixed Output Value : Defines the value to be output on DAC/PWM when fixed output mode is selected.<BR> Byte    2: Value to be output on DAC/PWM, Range -128 to 127 Bytes 3-5: Reserved must be set to 0x000000<BR><BR> <br>Note : To use Subframe Filter Value and Subframe Watch Dog care must be taken to set a value which approximately 10% more than 2x of the operating frequency. <BR> For example - 4K @ 60Hz, the value can be set as (1/(60*2))*1.10*10^6 = 9166us. <br><br>This command must be followed with a Write Execute Display command to be applied.<br> <br>"
    global Summary
    Summary.Command = "Write Xpr Actuator Waveform Control Parameter"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 4;
    try:
        writebytes=list(struct.pack('B',70))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',XprCommand.value)))
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        writebytes.extend(list(struct.pack('I',Data)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadXprActuatorWaveformControlParameter(XprCommand,  AwcChannel):
    "This command returns the specified parameter set to the AWC waveform generator.<br> Note : This command is supposed to be used only during the normal operating mode and not during the standby state. <br>"
    global Summary
    Summary.Command = "Read Xpr Actuator Waveform Control Parameter"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 4;
    try:
        writebytes=list(struct.pack('B',70))
        ProtocolData.OpcodeLength = 1;
        writebytes.extend(list(struct.pack('B',XprCommand.value)))
        writebytes.extend(list(struct.pack('B',AwcChannel.value)))
        readbytes = _readcommand(4, writebytes, ProtocolData)
        Data = struct.unpack_from ('I', bytearray(readbytes), 0)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, Data

def WriteTpgHorizontalRamp(RampColor,  RampStep):
    "This command sets the Horizontal Ramp test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Horizontal Ramp"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x01]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',RampColor.value)))
        valueArray = [0x00]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('H',RampStep.value)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgHorizontalRamp():
    "This command gets the Horizontal Ramp test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Horizontal Ramp"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        RampColorObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        RampStepObj = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgColorT(RampColorObj), TpgHorzRampStepT(RampStepObj)

def WriteTpgVerticalRamp(RampColor,  RampStep):
    "This command sets the Vertical Ramp test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Vertical Ramp"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x02]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',RampColor.value)))
        valueArray = [0x00]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('H',RampStep.value)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgVerticalRamp():
    "This command gets the Vertical Ramp test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Vertical Ramp"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        RampColorObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        RampStepObj = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgColorT(RampColorObj), TpgVertRampStepT(RampStepObj)

def WriteTpgHorizontalLines(LineColor,  BackgroundColor,  LineWidth,  DistBetweenLines):
    "This command sets the Horizontal Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Horizontal Lines"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x03]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',LineColor.value)))
        writebytes.extend(list(struct.pack('B',BackgroundColor.value)))
        writebytes.extend(list(struct.pack('H',LineWidth)))
        writebytes.extend(list(struct.pack('H',DistBetweenLines)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgHorizontalLines():
    "This command gets the Horizontal Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Horizontal Lines"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        LineColorObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        BackgroundColorObj = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        LineWidth = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
        DistBetweenLines = struct.unpack_from ('H', bytearray(readbytes), 5)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgColorT(LineColorObj), TpgColorT(BackgroundColorObj), LineWidth, DistBetweenLines

def WriteTpgDiagonalLines(LineColor,  BackgroundColor,  DistBetweenLines):
    "This command sets the Diagonal Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Diagonal Lines"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x04]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',LineColor.value)))
        writebytes.extend(list(struct.pack('B',BackgroundColor.value)))
        writebytes.extend(list(struct.pack('H',DistBetweenLines.value)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgDiagonalLines():
    "This command gets the Diagonal Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Diagonal Lines"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        LineColorObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        BackgroundColorObj = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        DistBetweenLinesObj = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgColorT(LineColorObj), TpgColorT(BackgroundColorObj), TpgLegalDistT(DistBetweenLinesObj)

def WriteTpgVerticalLines(LineColor,  BackgroundColor,  DistBetweenLines):
    "This command sets the Vertical Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Vertical Lines"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x05]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',LineColor.value)))
        writebytes.extend(list(struct.pack('B',BackgroundColor.value)))
        writebytes.extend(list(struct.pack('H',DistBetweenLines)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgVerticalLines():
    "This command gets the Vertical Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Vertical Lines"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        LineColorObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        BackgroundColorObj = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        DistBetweenLines = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgColorT(LineColorObj), TpgColorT(BackgroundColorObj), DistBetweenLines

def WriteTpgGrid(TpgGrid):
    "This command sets the Grid Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Grid"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x06]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',TpgGrid.LineColor.value)))
        writebytes.extend(list(struct.pack('B',TpgGrid.BackgroundColor.value)))
        writebytes.extend(list(struct.pack('H',TpgGrid.HorzWidth)))
        writebytes.extend(list(struct.pack('H',TpgGrid.VertWidth)))
        writebytes.extend(list(struct.pack('H',TpgGrid.HorzDistBetweenLines)))
        writebytes.extend(list(struct.pack('H',TpgGrid.VertDistBetweenLines)))
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgGrid():
    "This command gets the Grid Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Grid"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        TpgGrid.LineColor = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        TpgGrid.BackgroundColor = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        TpgGrid.HorzWidth = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
        TpgGrid.VertWidth = struct.unpack_from ('H', bytearray(readbytes), 5)[0]
        TpgGrid.HorzDistBetweenLines = struct.unpack_from ('H', bytearray(readbytes), 7)[0]
        TpgGrid.VertDistBetweenLines = struct.unpack_from ('H', bytearray(readbytes), 9)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgGrid

def WriteTpgCheckerboard(TopLeftCheckerColor,  NextCheckerColor,  NoOfHorzCheckers,  NoOfVertCheckers):
    "This command sets the Checkerboard test pattern and its related parameters. In the case where the desired pattern does not evenly divide across the DMD, there may be apparent mis-alignments along the border."
    global Summary
    Summary.Command = "Write Tpg Checkerboard"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x07]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',TopLeftCheckerColor.value)))
        writebytes.extend(list(struct.pack('B',NextCheckerColor.value)))
        writebytes.extend(list(struct.pack('H',NoOfHorzCheckers)))
        writebytes.extend(list(struct.pack('H',NoOfVertCheckers)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgCheckerboard():
    "This command gets the Checkerboard test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Checkerboard"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        TopLeftCheckerColorObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        NextCheckerColorObj = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        NoOfHorzCheckers = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
        NoOfVertCheckers = struct.unpack_from ('H', bytearray(readbytes), 5)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgColorT(TopLeftCheckerColorObj), TpgColorT(NextCheckerColorObj), NoOfHorzCheckers, NoOfVertCheckers

def WriteTpgColorbars():
    "This command sets the Colorbars test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Colorbars"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x08]
        writebytes.extend(valueArray)
        valueArray = [0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def WriteTpgMultiColorHorizontalRamp(RampStep):
    "This command sets the Multi Color Horizontal Ramp test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Multi Color Horizontal Ramp"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x09]
        writebytes.extend(valueArray)
        valueArray = [0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('H',RampStep.value)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgMultiColorHorizontalRamp():
    "This command gets the Multi Color Horizontal Ramp test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Multi Color Horizontal Ramp"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        RampStepObj = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgHorzRampStepT(RampStepObj)

def WriteTpgFixedStepHorizontalRamp(RampColor,  InitialIntensityValue,  NoOfSteps):
    "This command sets the Fixed Step Horizontal Ramp test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Fixed Step Horizontal Ramp"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x0A]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',RampColor.value)))
        valueArray = [0x00]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('H',InitialIntensityValue)))
        writebytes.extend(list(struct.pack('H',NoOfSteps)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgFixedStepHorizontalRamp():
    "This command gets the Fixed Step Horizontal Ramp test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Fixed Step Horizontal Ramp"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        RampColorObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        InitialIntensityValue = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
        NoOfSteps = struct.unpack_from ('H', bytearray(readbytes), 5)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgColorT(RampColorObj), InitialIntensityValue, NoOfSteps

def WriteTpgDiamondDiagonalLines(ForwardDiagStartColor,  BackwardDiagColor,  DoubleLineMode,  DistBetweenLines):
    "This command sets the Diamond Diagonal Lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Write Tpg Diamond Diagonal Lines"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        valueArray = [0x0B]
        writebytes.extend(valueArray)
        writebytes.extend(list(struct.pack('B',ForwardDiagStartColor.value)))
        writebytes.extend(list(struct.pack('B',BackwardDiagColor.value)))
        writebytes.extend(list(struct.pack('H',DoubleLineMode.value)))
        writebytes.extend(list(struct.pack('H',DistBetweenLines.value)))
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        valueArray = [0x00, 0x00]
        writebytes.extend(valueArray)
        _writecommand(writebytes, ProtocolData)
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful == False
    finally:
        return Summary

def ReadTpgDiamondDiagonalLines():
    "This command gets the Diamond Diagonal lines test pattern and its related parameters."
    global Summary
    Summary.Command = "Read Tpg Diamond Diagonal Lines"
    Summary.Successful = True
    global ProtocolData
    ProtocolData.CommandDestination = 1;
    try:
        writebytes=list(struct.pack('B',165))
        ProtocolData.OpcodeLength = 1;
        readbytes = _readcommand(11, writebytes, ProtocolData)
        ForwardDiagStartColorObj = struct.unpack_from ('B', bytearray(readbytes), 1)[0]
        BackwardDiagColorObj = struct.unpack_from ('B', bytearray(readbytes), 2)[0]
        DoubleLineModeObj = struct.unpack_from ('H', bytearray(readbytes), 3)[0]
        LegalDistBetweenLinesObj = struct.unpack_from ('H', bytearray(readbytes), 5)[0]
    except ValueError as ve:
        print("Exception Occurred ", ve)
        Summary.Successful = False
    finally:
        return Summary, TpgForwardDiagColorT(ForwardDiagStartColorObj), TpgBackwardDiagColorT(BackwardDiagColorObj), TpgDoubleLineModeT(DoubleLineModeObj), TpgLegalDistT(LegalDistBetweenLinesObj)

