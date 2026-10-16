from .CorrectionsCore import CppProvider, declareProviderHeader


class LumiFilter:
    def __init__(self, lumi_json_file):
        declareProviderHeader("lumi.h")
        self.provider = CppProvider("LumiFilter", lumi_json_file)

    def filter(self, df):
        return df.Filter(
            f"{self.provider.ref}->Pass(run, luminosityBlock)", "LumiFilter"
        )
