#  Copyright 2022, Lefebvre Dalloz Services
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import argparse

import numpy as np
import tritonclient.http

from transformer_deploy.benchmarks.utils import setup_logging


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="require inference", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--length", required=True, help="sequence length", choices=(16, 256), type=int)
    parser.add_argument("--model", required=True, help="model type", choices=("onnx", "tensorrt"))
    parser.add_argument("--url", default="127.0.0.1:8000", help="REST API endpoint. Default is localhost:8000", type=str)
    parser.add_argument("--model-version", default="1", help="model version", type=str)
    parser.add_argument("--batch-size", default=1, help="batch size", type=int)
    args, _ = parser.parse_known_args()

    setup_logging()
    model_name = f"transformer_{args.model}_inference"

    if args.length == 256:
        question = "Which name is also used to describe the Amazon rainforest in English?"
        text = """The Amazon rainforest (Portuguese: Floresta Amazônica or Amazônia; Spanish: Selva Amazónica,
         Amazonía or usually Amazonia; French: Forêt amazonienne; Dutch: Amazoneregenwoud), also known in 
         English as Amazonia or the Amazon Jungle, is a moist broadleaf forest that covers most of the 
         Amazon basin of South America. This basin encompasses 7,000,000 square kilometres (2,700,000 sq mi), 
         of which 5,500,000 square kilometres (2,100,000 sq mi) are covered by the rainforest. 
         This region includes territory belonging to nine nations. The majority of the forest is contained 
         within Brazil, with 60% of the rainforest, followed by Peru with 13%, Colombia with 10%, and with 
         minor amounts in Venezuela, Ecuador, Bolivia, Guyana, Suriname and French Guiana. States or departments 
         in four nations contain "Amazonas" in their names. The Amazon represents over half of the planet's 
         remaining rainforests, and comprises the largest and most biodiverse tract of tropical rainforest in 
         the world, with an estimated 390 billion individual trees divided into 16,000 species."""  # noqa: W291
    else:
        question = "Where do I live?"
        text = "My name is Wolfgang and I live in Berlin"

    triton_client = tritonclient.http.InferenceServerClient(url=args.url, verbose=False)
    assert triton_client.is_model_ready(
        model_name=model_name, model_version=args.model_version
    ), f"model {model_name} not yet ready"

    model_metadata = triton_client.get_model_metadata(model_name=model_name, model_version=args.model_version)
    model_config = triton_client.get_model_config(model_name=model_name, model_version=args.model_version)

    question_input = tritonclient.http.InferInput(name="QUESTION", shape=(args.batch_size,), datatype="BYTES")
    context_input = tritonclient.http.InferInput(name="CONTEXT", shape=(args.batch_size,), datatype="BYTES")
    output = tritonclient.http.InferInput(name="output", shape=(args.batch_size,), datatype="BYTES")

    question_input.set_data_from_numpy(np.asarray([question] * args.batch_size, dtype=object))
    context_input.set_data_from_numpy(np.asarray([text] * args.batch_size, dtype=object))
    response = triton_client.infer(
        model_name=model_name,
        model_version=args.model_version,
        inputs=[question_input, context_input],
        outputs=[output],
    )

    print(response.get_response())
