from pprint import pformat
from sys import stdout

from androguard.core.analysis.analysis import ExternalMethod
from androguard.misc import AnalyzeDex
from loguru import logger
from code_parse import handler


def generate_param_names(params, is_static):
    """
    生成参数列表
    :param is_static: 是否是静态方法
    :param params: 参数类型列表
    :return: 参数列表
    """
    param_names = []
    reg_index = 0 if is_static else 1  # 非静态方法参数从 p1 开始

    # 非静态方法：添加 this 参数（p0）
    if not is_static:
        param_names.append([['TypeName', ('this', 0)], ['Local', f'p0']])

    # 遍历参数类型，分配寄存器
    for param in params:
        param_type = param[1][0]
        dim = param[1][1]

        # 检查是否为宽类型（long/double）
        is_wide = (param_type in ('J', 'D')) and (dim == 0)

        # 添加当前参数名（例如 p1）
        param_names.append([[param[0], param[1]], ['Local', f'p{reg_index}']])

        # 更新寄存器索引（宽类型占2个）
        reg_index += 2 if is_wide else 1

    return param_names


def convert_method(method):
    """提取AST树"""

    # 外部方法无法提取代码
    if isinstance(method, ExternalMethod):
        return None

    # 获取方法基本信息
    method_class = method.get_class_name()[1:-1].replace('/', '.')
    method_name = method.get_name()
    method_descriptor_list = method.get_descriptor()[1:].split(')')

    # 构建方法triple
    triple = (
        method_class,
        method_name,
        method.get_descriptor()
    )

    # 解析返回类型
    return_type = method_descriptor_list[1]
    return_type = return_type.removesuffix(';')
    ret = ['TypeName', (return_type, return_type.count('['))]

    # 解析函数修饰符
    flags = method.get_access_flags_string().split(' ')

    # 解析参数
    params = []
    params_temp = method_descriptor_list[0].split(';')[:-1]
    is_static = True if 'static' in flags else False
    for i in range(len(params_temp)):
        params_temp[i] = params_temp[i].strip()
    for param in params_temp:
        temp = ['TypeName', (param, param.count('['))]
        params.append(temp)
    params = generate_param_names(params, is_static)

    # 构建方法体AST
    ast_body = handler.build_body(method, is_static)

    return {
        'body': ast_body,
        'comments': [],
        'flags': flags,
        'params': params,
        'ret': ret,
        'triple': triple
    }


def dex_to_ast(dex_path):
    _, _, dx = AnalyzeDex(dex_path)
    results = []
    for method in dx.get_methods():
        result = convert_method(method.method)
        if result:
            results.append(result)
    return results


def main():
    logger.remove(0)
    logger.add(stdout, colorize=True, level='INFO')
    logger.info('')
    results = dex_to_ast("../dex_output/test/test.dex")
    # for i in results:
    #     logger.debug(f'\n{pformat(i)}')
    logger.info('')


if __name__ == '__main__':
    main()
