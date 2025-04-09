"""
提供对外接口
"""
from gensim.models import Doc2Vec
from loguru import logger
from .node2ast import convert_method
from .ast2vec import ast_to_vector


class AstFeatureClass:
    def __init__(self, method=None):
        self.method = method
        self.model = Doc2Vec.load("models/ast2vec_model.model")

    def extract_feature(self):
        """
        提取特征
        :return: 返回特征值
        """
        ast = convert_method(self.method)
        if ast is None:
            return False, [0] * 200
        vector = ast_to_vector(str(ast), self.model)
        return True, vector

    def print(self):
        """输出方法"""
        logger.debug(self.method)


AstFeature = AstFeatureClass()
