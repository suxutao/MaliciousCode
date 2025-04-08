from gensim.models import Doc2Vec
from gensim.models.doc2vec import TaggedDocument
import re
from loguru import logger


def ast_tokenizer(ast_text):
    """
    自定义AST文本分词函数，保留结构符号
    :param ast_text: AST文本
    :return: 分词后的结果
    """
    # 替换换行符和多余空格
    ast_text = ast_text.replace('\n', ' ').strip()
    # 使用正则表达式分割，保留'['和']'
    tokens = re.findall(r'\[|]|[^\[\]\s]+', ast_text)
    return tokens


def prepare_ast_corpus(ast_texts):
    """将AST文本转换为TaggedDocument格式"""
    corpus = []
    for idx, ast in enumerate(ast_texts):
        tokens = ast_tokenizer(ast)
        corpus.append(TaggedDocument(tokens, tags=[f"ast_{idx}"]))
    return corpus


def ast_to_vector(ast_text, model):
    """生成AST向量表示"""
    tokens = ast_tokenizer(ast_text)
    vector = model.infer_vector(tokens)
    return vector


def main():
    # 示例AST文本（模拟论文中的Listing 2）
    example_ast = """
    ['body': ['BlockStatement', None,
        'ExpressionStatement', ['Assignment',
            'FieldAccess', ['Local', 'this'],
            'com/tencent/qqgame/installer/i, a',
            'com/tencent/qqgame/installer/QQGameInstaller;'],
        ['Local', 'p1']],
        'ReturnStatement', None]
    """
    #
    # # 假设有多个AST文本（示例数据）
    # ast_texts = [example_ast] * 1000  # 实际需替换为真实AST数据集
    # corpus = prepare_ast_corpus(ast_texts)
    #
    # # 训练Doc2Vec模型
    # model = Doc2Vec(
    #     documents=corpus,
    #     vector_size=200,  # 向量维度（论文参数）
    #     window=5,  # 上下文窗口
    #     min_count=1,  # 忽略低频词
    #     workers=8,  # 并行线程数
    #     epochs=50  # 训练轮次
    # )

    # 保存模型
    # model.save("../models/ast2vec_model.model")
    # 加载模型（推理时）
    model = Doc2Vec.load("../models/ast2vec_model.model")

    # 示例：生成单个AST的向量
    logger.info(f"\n{model.dv['ast_1']}")
    ast_vector = ast_to_vector(example_ast, model)
    logger.info(f"\n{ast_vector}")


if __name__ == '__main__':
    main()
