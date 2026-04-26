class StreamlitPortfolioLoader(PortfolioInputSource):
    def __init__(self, form_data: dict):
        self.form_data = form_data

    def load(self) -> SchemaFrame:
        df = pd.DataFrame([self.form_data])
        return SchemaFrame(df, columns=..., dtypes=..., label="Streamlit Portfolio")
