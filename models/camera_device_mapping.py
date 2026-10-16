
CAMERA_DEVICE_NAMES = {
    "D01": "Samsung S3Mini",
    "D02": "Apple iPhone4s",
    "D03": "Huawei P9",
    "D04": "LG D290",
    "D05": "Apple iPhone5c",
    "D06": "Apple iPhone6",
    "D07": "Lenovo P70A",
    "D08": "Samsung Tab3",
    "D09": "Apple iPhone4",
    "D10": "Apple iPhone4s",
    "D11": "Samsung S3",
    "D12": "Sony XperiaZ1Compact",
    "D13": "Apple iPad2",
    "D14": "Apple iPhone5c",
    "D15": "Apple iPhone6",
    "D16": "Huawei P9Lite",
    "D17": "Microsoft Lumia640LTE",
    "D18": "Apple iPhone5c",
    "D19": "Apple iPhone6p",
    "D20": "Apple iPadMini",
    "D21": "Wiko Ridge4G",
    "D22": "Samsung TrendPlus",
    "D23": "Asus Zenfone2Laser",
    "D24": "Xiaomi RedmiNote3",
    "D25": "Oneplus A3000",
    "D26": "Samsung S3Mini",
    "D27": "Samsung S5",
    "D28": "Huawei P8",
    "D29": "Apple iPhone5",
    "D30": "Huawei Honor5c",
    "D31": "Samsung S4Mini",
    "D32": "Oneplus A3003",
    "D33": "Huawei Ascend",
    "D34": "Apple iPhone5",
    "D35": "Samsung TabA",
}


def get_device_name(camera_id):
    """Map a dataset camera ID to its documented device name."""
    if camera_id is None:
        return None

    camera_id = str(camera_id).strip().upper()

    return CAMERA_DEVICE_NAMES.get(
        camera_id,
        f"Unknown device model ({camera_id})"
    )
