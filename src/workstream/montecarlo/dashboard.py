from simulation.workstreams.montecarlo.summary import summarize_withdrawal_outcomes

def diagnostic_dashboard(context: SimulationContext, 
                         sim_results, config, folder='.', export_excel_name='diagnostic_output.xlsx', export_pdf_name='diagnostic_charts.pdf'):
    excel_path = os.path.join(folder, export_excel_name)
    pdf_path = os.path.join(folder, export_pdf_name)

    # Perform your usual analysis and save files to the paths above
    analyze_montecarlo_rmd_timing(
        df_sim_results=sim_results,
        config=config,
        export_excel_path=excel_path,
        export_pdf_path=pdf_path
    )

    print(f'📁 Dashboard files saved to: {folder}')
