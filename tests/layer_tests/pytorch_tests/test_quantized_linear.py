# Copyright (C) 2018-2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
import torch
import numpy as np
from pytorch_layer_test_class import PytorchLayerTest

class TestQuantizedLinear(PytorchLayerTest):
    def _prepare_input(self, input_shape=(2, 2)):
        return (np.random.randn(*input_shape).astype(np.float32),)

    def create_model(self, weight_shape, is_bias, scale, zero_point):

        class aten_quantized_linear(torch.nn.Module):
            def __init__(self, weight_shape, is_bias, scale, zero_point):
                super(aten_quantized_linear, self).__init__()
                if is_bias:
                    self.linear = torch.ao.nn.quantized.Linear(weight_shape[-1], weight_shape[0], True)
                    torch.nn.init.normal_(self.linear.bias())
                else:
                    self.linear = torch.ao.nn.quantized.Linear(weight_shape[-1], weight_shape[0], False)
                self.linear.scale = float(scale)
                self.linear.zero_point = int(zero_point)

            def forward(self, inp):
                inp_q = torch.quantize_per_tensor(inp, 1., 0, torch.quint8)
                return torch.dequantize(self.linear(inp_q))

        ref_net = None

        return aten_quantized_linear(weight_shape, is_bias, scale, zero_point), ref_net, "quantized::linear"

    @pytest.mark.parametrize("params", [
        {'input_shape': [3, 9], 'weight_shape': [10, 9]},
        {'input_shape': [3, 9], 'weight_shape': [9]},
        {'input_shape': [2, 3, 9], 'weight_shape': [10, 9]},
        {'input_shape': [2, 3, 9], 'weight_shape': [9]},
        {'input_shape': [3, 9], 'weight_shape': [9], "bias": True},
        {'input_shape': [3, 9], 'weight_shape': [10, 9], "bias": True},
        {'input_shape': [2, 3, 9], 'weight_shape': [10, 9], "bias": True},
    ])
    @pytest.mark.parametrize("scale", [1., 0.3, 1.3])
    @pytest.mark.parametrize("zero_point", [0, 1])
    @pytest.mark.parametrize("trace", [True, False])
    @pytest.mark.nightly
    @pytest.mark.precommit
    def test_quantized_linear(self, params, scale, zero_point, trace, ie_device, precision, ir_version):
        input_shape = params.get("input_shape")
        weight_shape = params.get("weight_shape")
        bias = params.get("bias", False)
        self._test(*self.create_model(weight_shape, bias, scale, zero_point), ie_device, precision, ir_version,
                   kwargs_to_prepare_input={"input_shape": input_shape}, trace_model=trace, freeze_model=False)