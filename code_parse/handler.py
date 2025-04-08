"""
指令处理器
"""
import re


def parse_field_desc(field_desc):
    """
    解析字段描述符，返回类名和字段名
    :param field_desc: 如 "Lcom/Class;->field:Ljava/lang/Object;"
    :return: (class_name, field_name)
    """
    # 分割类和字段部分
    class_part, field_part = field_desc.split('->')
    # 提取类名（去除开头的L和结尾的;）
    class_name = class_part[1:].split(':')[0].replace('/', '.')
    # 提取字段名（去除类型描述）
    field_name = field_part.split(':')[0]
    return class_name, field_name


def parse_method_descriptor(descriptor):
    """
    解析方法描述符，返回参数类型列表和返回类型
    :param descriptor: 方法描述符，如 "(Ljava/lang/String;IZ)V"
    :return: (params, ret_type)
    """
    # 提取参数部分和返回类型
    basic_map = {}
    match = re.match(r'^\((.*?)\)(.*)$', descriptor)
    if not match:
        return [], {'type': 'void', 'dim': 0}

    params_str, ret_str = match.groups()
    params = []
    i = 0

    # 解析参数类型
    while i < len(params_str):
        dim = 0
        while params_str[i] == '[':
            dim += 1
            i += 1

        if params_str[i] == 'L':
            end = params_str.index(';', i)
            type_name = params_str[i + 1:end].replace('/', '.')
            i = end + 1
        else:
            basic_map = {
                'V': 'void', 'Z': 'boolean', 'B': 'byte',
                'S': 'short', 'C': 'char', 'I': 'int',
                'J': 'long', 'F': 'float', 'D': 'double'
            }
            type_name = basic_map.get(params_str[i], 'unknown')
            i += 1

        params.append({'type': type_name, 'dim': dim})

    # 解析返回类型
    ret_dim = 0
    ret_char = ret_str[0]
    while ret_char == '[':
        ret_dim += 1
        ret_str = ret_str[1:]
        ret_char = ret_str[0]

    if ret_char == 'L':
        ret_type = ret_str[1:-1].replace('/', '.')
    else:
        ret_type = basic_map.get(ret_char, 'unknown')

    return params, {'type': ret_type, 'dim': ret_dim}


def parse_parameters(encoded_method, is_static):
    """
    解析方法的参数列表（寄存器分配 + 类型信息）
    :return: [
        {'reg': 'p0', 'type_info': {'type': 'this', 'dim': 0}},
        {'reg': 'p1', 'type_info': {'type': 'int', 'dim': 0}},
        ...
    ]
    """
    descriptor = encoded_method.get_descriptor()
    param_types, _ = parse_method_descriptor(descriptor)

    params = []
    reg_idx = 0 if is_static else 1  # 非静态方法 p0=this

    # 添加隐含的 this 参数
    if not is_static:
        params.append({
            'reg': 'p0',
            'type_info': {'type': 'this', 'dim': 0}
        })

    # 分配显式参数
    for p_type in param_types:
        reg = f'p{reg_idx}'
        params.append({
            'reg': reg,
            'type_info': {'type': p_type['type'], 'dim': p_type['dim']}
        })

        # 处理宽类型（long/double）
        if p_type['type'] in ('long', 'double') and p_type['dim'] == 0:
            reg_idx += 2
        else:
            reg_idx += 1

    return params


def parse_method_desc(method_desc):
    """
    解析方法描述符，如 "Lcom/Class;->method(Ljava/lang/String;)V"
    :return: (class_name, method_name)
    """
    if '->' not in method_desc:
        return None, None
    class_part, rest = method_desc.split('->')
    method_name = rest.split('(')[0]
    return class_part[1:].replace('/', '.'), method_name


def parse_two_operands(ins):
    """
    解析双操作数指令，如 "int-to-long v0, v1"
    :return: (dest_reg, src_reg)
    """
    parts = ins.get_output().split(', ')
    return parts[0].split()[-1].strip(), parts[1].strip()


def parse_operand(operand):
    """ 解析操作数为AST节点 """
    if operand.startswith('v'):
        return ['Local', operand]
    elif operand.startswith('p'):
        return ['Parameter', operand]
    elif '->' in operand:
        class_part, field = operand.split('->')
        return ['StaticFieldAccess', class_part[1:].replace('/', '.'), field.split(':')[0]]
    elif operand == 'this':
        return ['ThisReference']
    elif operand.isdigit():
        return ['Literal', int(operand)]
    elif operand.startswith('"'):
        return ['Literal', operand.strip('"')]
    else:
        return ['Unknown', operand]


def handle_return(op, ins):
    if op == 'return-void':
        return ['ReturnStatement', None]
    else:
        operand = parse_operand(ins.get_output().split()[-1])
        return ['ReturnStatement', operand]


def handle_cast(op, ins, regs):
    # 示例指令: int-to-long v0, v1
    dest_reg, src_reg = parse_two_operands(ins)
    from_type, to_type = op.split('-to-')

    # 更新寄存器类型
    regs[dest_reg] = {'type': to_type, 'dim': 0}

    return ['ExpressionStatement',
            ['Assignment',
             ['Local', dest_reg],
             ['CastExpression',
              to_type.upper(),
              parse_operand(src_reg)
              ]
             ]
            ]


def handle_invoke(op, ins):
    # 示例指令: invoke-virtual {v0}, Lcom/Class;->method()V
    parts = ins.get_output().split(', ')
    args_part = parts[0][parts[0].find('{') + 1:].split(', ')
    method_desc = parts[-1].strip()

    # 解析方法信息
    class_name, method_name = parse_method_desc(method_desc)
    if class_name is None:
        return None

    # 解析参数
    args = [parse_operand(arg.strip()) for arg in args_part]

    # 目标对象（非静态方法第一个参数为this）
    target = args[0] if 'static' not in op else None

    return ['ExpressionStatement',
            ['MethodInvocation',
             target,
             (class_name, method_name),
             args[1:] if target else args
             ]
            ]


def handle_arithmetic(op, ins):
    """
    处理算术运算指令：add-*, sub-*, mul-*, div-*, rem-*
    :param op: 指令名称（如 "add-int/2addr"）
    """
    # 解析指令输出（示例："v0, v1, v2" 或 "v0, v1"）
    operands = [o.strip() for o in ins.get_output().split(',')]

    # 处理不同指令格式
    if '/2addr' in op:  # 如 add-int/2addr v0, v1
        dest = operands[0]
        src = operands[1]
        return ['ExpressionStatement',
                ['Assignment',
                 parse_operand(dest),
                 ['BinaryExpression',
                  op.split('-')[0].upper(),
                  parse_operand(dest),
                  parse_operand(src)
                  ]
                 ]
                ]
    else:  # 常规二元运算（如 add-int v0, v1, v2）
        dest, src1, src2 = operands
        return ['ExpressionStatement',
                ['Assignment',
                 parse_operand(dest),
                 ['BinaryExpression',
                  op.split('-')[0].upper(),
                  parse_operand(src1),
                  parse_operand(src2)
                  ]
                 ]
                ]


def handle_bitwise(op, ins):
    """
    处理位运算指令：shl-*, shr-*, and-*, or-*, xor-*
    """
    # 分割操作数（示例："v0, v1, 0x1" 或 "v0, v1"）
    operands = [o.strip() for o in ins.get_output().split(',')]

    # 处理移位指令的特殊情况（含立即数）
    if any(c in op for c in ['lit8', 'lit16']):  # 如 shl-int/lit8 v0, v1, 0x3
        dest, src, imm = operands
        return ['ExpressionStatement',
                ['Assignment',
                 parse_operand(dest),
                 ['BinaryExpression',
                  op.split('-')[0].upper(),
                  parse_operand(src),
                  ['Literal', int(imm, 0)]
                  ]
                 ]
                ]
    else:  # 常规位运算
        if len(operands) == 2:  # /2addr 形式
            dest, src = operands
            src1 = dest
            src2 = src
        else:  # 三操作数形式
            dest, src1, src2 = operands

        return ['ExpressionStatement',
                ['Assignment',
                 parse_operand(dest),
                 ['BinaryExpression',
                  op.split('-')[0].upper(),
                  parse_operand(src1),
                  parse_operand(src2)
                  ]
                 ]
                ]


def handle_control_flow(op, ins):
    """
    处理条件跳转指令：if-*
    """
    # 解析条件类型（如 "eq", "nez"）
    cond_type = op.split('-')[1]
    # 分割操作数（示例："v0, :label_123" 或 "v0, v1, :label_456"）
    parts = [p.strip() for p in ins.get_output().split(',')]

    # 处理不同条件格式
    if cond_type.endswith('z'):  # 单操作数条件（如 if-eqz）
        reg, label = parts[0].split()[-1], parts[1]
        condition = ['UnaryExpression',
                     CONDITION_MAP[cond_type],
                     parse_operand(reg)
                     ]
    else:  # 双操作数条件（如 if-ge）
        reg1, reg2, label = parts[0].split()[-1], parts[1], parts[2]
        condition = ['BinaryExpression',
                     CONDITION_MAP[cond_type],
                     parse_operand(reg1),
                     parse_operand(reg2)
                     ]

    return ['IfStatement',
            condition,
            ['GotoStatement', label.strip(':')]
            ]


def handle_array_access(op, ins):
    """
    处理数组访问指令：aget-*, aput-*
    """
    operands = [o.strip() for o in ins.get_output().split(',')]

    if op.startswith('aget'):  # 数组读取
        dest, array, index = operands
        return ['ExpressionStatement',
                ['Assignment',
                 parse_operand(dest),
                 ['ArrayAccess',
                  parse_operand(array),
                  parse_operand(index)
                  ]
                 ]
                ]
    else:  # 数组写入（aput）
        value, array, index = operands
        return ['ExpressionStatement',
                ['Assignment',
                 ['ArrayAccess',
                  parse_operand(array),
                  parse_operand(index)
                  ],
                 parse_operand(value)
                 ]
                ]


def handle_object_creation(ins, regs):
    """
    处理对象创建指令：new-instance
    """
    # 示例指令："new-instance v0, Ljava/lang/Object;"
    parts = [p.strip() for p in ins.get_output().split(',')]
    dest_reg = parts[0].split()[-1]
    class_desc = parts[1]

    # 解析类名（去除开头的L和结尾的;）
    class_name = class_desc[1:-1].replace('/', '.')

    # 更新寄存器类型
    regs[dest_reg] = {'type': class_name, 'dim': 0}

    return ['ExpressionStatement',
            ['Assignment',
             ['Local', dest_reg],
             ['NewInstance', class_name]
             ]
            ]


# 常量定义
CONDITION_MAP = {
    'eq': '==', 'ne': '!=',
    'lt': '<', 'le': '<=',
    'gt': '>', 'ge': '>=',
    'eqz': '==', 'nez': '!=',
    'ltz': '<', 'lez': '<=',
    'gtz': '>', 'gez': '>='
}


def handle_field_access(ins):
    # 示例指令: iget-object v0, p0, Lcom/Class;->field:Ljava/lang/Object;
    parts = ins.get_output().split(', ')
    dest_reg = parts[0].split()[-1]
    obj_reg = parts[1]
    field_desc = parts[2]

    # 解析字段信息
    class_name, field_name = parse_field_desc(field_desc)

    return ['ExpressionStatement',
            ['Assignment',
             parse_operand(dest_reg),
             ['FieldAccess',
              parse_operand(obj_reg),
              (class_name, field_name)
              ]
             ]
            ]


def dispatch_instruction(op, ins, regs):
    """ 指令分派 """
    if op.startswith('return'):
        return handle_return(op, ins)
    elif '-to-' in op:
        return handle_cast(op, ins, regs)
    elif op.startswith('invoke'):
        return handle_invoke(op, ins)
    elif op.startswith(('iget', 'iput')):
        return handle_field_access(ins)
    elif op.startswith(('add', 'sub', 'mul', 'div', 'rem')):
        return handle_arithmetic(op, ins)
    elif op.startswith(('shl', 'shr', 'and', 'or', 'xor')):
        return handle_bitwise(op, ins)
    elif op.startswith('if-'):
        return handle_control_flow(op, ins)
    elif op.startswith(('aget', 'aput')):
        return handle_array_access(op, ins)
    elif op.startswith('new-'):
        return handle_object_creation(ins, regs)
    else:
        return None


def build_body(encoded_method, is_static):
    # 初始化参数和寄存器类型
    params = parse_parameters(encoded_method, is_static)
    registers = {p['reg']: p['type_info'] for p in params}

    # 构建方法体
    body = []
    for ins in encoded_method.get_instructions():
        op = ins.get_name()
        stmt = dispatch_instruction(op, ins, registers)
        if stmt:
            body.append(stmt)

    return ['BlockStatement', None, body]
