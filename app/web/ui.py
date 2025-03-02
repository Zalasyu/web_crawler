import gradio as gr
import requests
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List, Any

BASE_URL = "http://localhost:8000"

def fetch_data(endpoint: str, params: Dict[str, str] = None) -> Any:
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
    response.raise_for_status()
    return response.json()

def trigger_monitor(agency_slug: str, title: str, start_date: str, end_date: str):
    response = requests.post(f"{BASE_URL}/monitor/{agency_slug}/{title}?start_date={start_date}&end_date={end_date}")
    response.raise_for_status()
    return response.json()["message"]

def update_titles(agency_slug: str):
    if not agency_slug:
        return gr.update(choices=[])
    titles = fetch_data(f"titles/{agency_slug}")
    return gr.update(choices=[(str(t), str(t)) for t in titles])

def plot_word_count(word_counts: Dict[str, int]):
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=list(word_counts.keys()), y=list(word_counts.values()), ax=ax, palette="viridis")
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Agency")
    plt.ylabel("Word Count")
    plt.title("Word Count per Agency")
    plt.tight_layout()
    return fig

def plot_changes(changes: List[List[Any]]):
    fig, ax = plt.subplots(figsize=(10, 6))
    dates, counts = zip(*changes) if changes else ([], [])
    ax.plot(dates, counts, marker='o')
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Date")
    plt.ylabel("Change Count")
    plt.title("Historical Changes Over Time")
    plt.tight_layout()
    return fig

def main_interface(agency_slug: str, title: str, start_date: str, end_date: str):
    monitor_msg = trigger_monitor(agency_slug, title, start_date, end_date) if agency_slug and title and start_date and end_date else "Select an agency, title, and date range to monitor."

    word_counts = fetch_data("word_count_per_agency")
    changes = fetch_data("historical_changes", {"start_date": start_date, "end_date": end_date})
    keywords = fetch_data("keywords")
    
    word_count_plot = plot_word_count(word_counts)
    changes_plot = plot_changes(changes)
    
    keywords_str = "\n".join(f"{word}: {count}" for word, count in keywords)
    
    return word_count_plot, changes_plot, keywords_str, monitor_msg

agencies = requests.get(f"{BASE_URL}/agencies").json()
agency_options = [(agency["display_name"], agency["slug"]) for agency in agencies]

with gr.Blocks(title="eCFR Analyzer") as demo:
    gr.Markdown("# eCFR Analyzer")
    
    with gr.Row():
        with gr.Column():
            agency_input = gr.Dropdown(choices=agency_options, label="Select Agency")
            title_input = gr.Dropdown(choices=[], label="Select Title")
            start_date_input = gr.Textbox(label="Start Date (YYYY-MM-DD)", value="2025-02-09")
            end_date_input = gr.Textbox(label="End Date (YYYY-MM-DD)", value="2025-02-27")
            analyze_btn = gr.Button("Analyze")
        with gr.Column():
            word_count_output = gr.Plot(label="Word Count per Agency")
    
    with gr.Row():
        changes_output = gr.Plot(label="Historical Changes Over Time")
    
    with gr.Row():
        keywords_output = gr.Textbox(label="Top Keywords")
    
    monitor_status = gr.Textbox(label="Monitor Status")
    
    agency_input.change(fn=update_titles, inputs=agency_input, outputs=title_input)
    analyze_btn.click(fn=main_interface, inputs=[agency_input, title_input, start_date_input, end_date_input], 
                      outputs=[word_count_output, changes_output, keywords_output, monitor_status])

demo.launch()