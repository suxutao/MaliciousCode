"""
把apk文件反编译为dex文件
"""
import os
import shutil
from loguru import logger

from androguard.core.bytecodes.apk import APK


def clear_folder(folder_path):
    """
    清空文件夹
    :param folder_path: 文件夹路径
    """

    try:
        # 遍历文件夹及其子文件夹
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # 删除文件
                os.remove(file_path)
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                # 删除子文件夹
                shutil.rmtree(dir_path)
    except Exception as e:
        logger.info(f"清空文件夹时出现错误: {e}")



def apk_to_dex(apk_path, output_dir, relative_path):
    """
    把一个 apk 文件反编译成 dex 文件
    :param apk_path: apk文件目录
    :param output_dir: 输出目录
    :param relative_path: 拼接的相对目录
    """

    try:
        # 加载 APK 文件
        apk = APK(apk_path)
        # 获取 APK 中的所有 DEX 文件
        dex_files = apk.get_all_dex()
        # 获取 APK 文件名（不包含扩展名）
        apk_name = os.path.splitext(os.path.basename(apk_path))[0]
        # 构建输出目录，包含相对路径
        apk_output_dir = os.path.join(output_dir, relative_path)
        os.makedirs(apk_output_dir, exist_ok=True)

        for i, dex in enumerate(dex_files):
            # 生成输出 DEX 文件的路径
            output_path = os.path.join(apk_output_dir, f"{apk_name}{i + 1}.dex" if i > 0 else f"{apk_name}.dex")
            # 将 DEX 文件写入到指定路径
            with open(output_path, 'wb') as f:
                f.write(dex)
            logger.success(f"DEX file saved to {output_path}")
    except Exception as e:
        logger.error(f"An error occurred while processing {apk_path}: {e}")


def batch_apk_to_dex(apk_dir, output_dir):
    """
    把一个目录下的 apk 文件全部反编译成 dex 文件
    :param apk_dir: apk 目录
    :param output_dir: 输出目录
    """
    # 检查 APK 目录是否存在
    if not os.path.exists(apk_dir):
        logger.error(f"The APK directory {apk_dir} does not exist.")
        return
    # 检查输出目录是否存在，不存在则创建
    os.makedirs(output_dir, exist_ok=True)
    clear_folder(output_dir)
    total_apks = 0
    processed_apks = 0
    # 遍历 APK 目录及其所有子目录
    for root, dirs, files in os.walk(apk_dir):
        for file in files:
            if file.endswith('.apk'):
                total_apks += 1
                apk_path = os.path.join(root, file)
                # 计算相对路径
                relative_path = os.path.relpath(root, apk_dir)
                logger.info(f"Processing {apk_path}...")

                apk_to_dex(apk_path, output_dir, relative_path)
                processed_apks += 1
    logger.success(f"Total APKs found: {total_apks}, Processed: {processed_apks}")


def main():
    # 包含多个 APK 文件的多层嵌套目录
    apk_dir = "data"
    # 输出 DEX 文件的根目录
    output_dir = "dex_output"

    batch_apk_to_dex(apk_dir, output_dir)


if __name__ == "__main__":
    main()
