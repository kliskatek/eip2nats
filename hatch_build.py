"""
Custom build hook for hatchling.

Forces the wheel to be tagged as platform-specific (not pure Python)
since it contains pre-compiled C++ extensions (.so/.pyd) and shared
libraries (.so/.dll) built by the scripts in scripts/.
"""

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        build_data["pure_python"] = False
        build_data["infer_tag"] = True
