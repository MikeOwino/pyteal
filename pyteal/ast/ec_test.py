from typing import Callable

import pytest

import pyteal as pt

OPERATIONS: list[
    tuple[
        Callable[[pt.EllipticCurve, pt.Expr], pt.Expr]
        | Callable[[pt.EllipticCurve, pt.Expr, pt.Expr], pt.Expr],
        pt.Op,
        int,
    ]
] = [
    (pt.EcAdd, pt.Op.ec_add, 2),
    (pt.EcScalarMul, pt.Op.ec_scalar_mul, 2),
    (pt.EcPairingCheck, pt.Op.ec_pairing_check, 2),
    (pt.EcMultiScalarMul, pt.Op.ec_multi_scalar_mul, 2),
    (pt.EcSubgroupCheck, pt.Op.ec_subgroup_check, 1),
    (pt.EcMapTo, pt.Op.ec_map_to, 1),
]


def test_EcOperation():
    for operation, expected_op, num_args in OPERATIONS:
        for curve in pt.EllipticCurve:
            args = [pt.Bytes(f"arg{i}") for i in range(num_args)]
            expr = operation(curve, *args)
            assert expr.type_of() == pt.TealType.bytes

            expected = pt.TealSimpleBlock(
                [pt.TealOp(arg, pt.Op.byte, f'"arg{i}"') for i, arg in enumerate(args)]
                + [pt.TealOp(expr, expected_op, curve.arg_name)]
            )

            actual, _ = expr.__teal__(pt.CompileOptions(version=10))
            actual.addIncoming()
            actual = pt.TealBlock.NormalizeBlocks(actual)

            assert actual == expected

            # Test wrong arg types
            for i in range(num_args):
                bad_args = args.copy()
                bad_args[i] = pt.Int(1)
                with pytest.raises(pt.TealTypeError):
                    operation(curve, *bad_args)
