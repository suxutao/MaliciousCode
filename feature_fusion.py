from androguard.misc import AnalyzeDex
from loguru import logger

from code_parse.feature import AstFeatureClass

AstFeature=AstFeatureClass()

def fusion(api_feature, ast_feature):
    """两部分特征融合"""
    return [api_feature, ast_feature]


def dex2feature(dex_path):
    """
    把dex文件转换为FCG及其特征
    :param dex_path: dex文件路径
    :return: FCG及其特征
    """
    _, _, dx = AnalyzeDex(dex_path)
    # 创建调用图
    call_graph = dx.get_call_graph()
    results = {}

    logger.debug('提取FCG完成')
    # 输出调用图
    for method in call_graph.nodes():
        api_feature = []
        AstFeature.method=method
        ast_feature = AstFeature.extract_feature()
        feature = fusion(api_feature, ast_feature)
        results.update({method: feature})

    return results


def main():
    logger.info('begin')
    dex_path = "dex_output/test/test.dex"
    result = dex2feature(dex_path)
    logger.info('end')
    for k, v in result.items():
        logger.success(f'{k}:{v[0]}')
        break


if __name__ == '__main__':
    main()
