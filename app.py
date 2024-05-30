import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('sankey-diagram-424912-a6f1f88ada06.json', scope)
client = gspread.authorize(creds)

# Load data from Google Sheets
spreadsheet_id = 'your_google_sheet_id'
sheet = client.open_by_key(spreadsheet_id)
flow_df = pd.DataFrame(sheet.worksheet('Flow').get_all_records())
campaigns_df = pd.DataFrame(sheet.worksheet('Campaigns').get_all_records())
contracts_df = pd.DataFrame(sheet.worksheet('Contracts').get_all_records())

# Prepare nodes and links for the Sankey diagram
labels = []
sources = []
targets = []
values = []

# Adding unique campaign types and their indices
campaign_type_labels = list(flow_df['Campaign Type'].unique())
campaign_type_indices = {label: i for i, label in enumerate(campaign_type_labels)}
labels.extend(campaign_type_labels)

# Adding campaign IDs and their indices
campaign_id_labels = list(flow_df['Campaign Name'])
campaign_id_indices = {label: i + len(labels) for i, label in enumerate(campaign_id_labels)}
labels.extend(campaign_id_labels)

# Adding contract types and their indices
contract_type_labels = list(contracts_df['Contract Type'].unique())
contract_type_indices = {label: i + len(labels) for i, label in enumerate(contract_type_labels)}
labels.extend(contract_type_labels)

# Adding contract IDs and their indices
contract_id_labels = list(contracts_df['Contract Name'])
contract_id_indices = {label: i + len(labels) for i, label in enumerate(contract_id_labels)}
labels.extend(contract_id_labels)

# Create links from campaign types to campaign IDs
for idx, row in flow_df.iterrows():
    campaign_type = row['Campaign Type']
    campaign_name = row['Campaign Name']
    campaign_type_idx = campaign_type_indices[campaign_type]
    campaign_id_idx = campaign_id_indices[campaign_name]
    
    sources.append(campaign_type_idx)
    targets.append(campaign_id_idx)
    values.append(1)  # You can adjust the value if necessary

# Create links from campaign IDs to contract types
for idx, row in flow_df.iterrows():
    campaign_name = row['Campaign Name']
    campaign_id_idx = campaign_id_indices[campaign_name]
    
    # Check each contract-related column
    contract_columns = flow_df.columns[5:]
    for col in contract_columns:
        if not pd.isna(row[col]) and row[col].strip() == 'X':  # Check for 'X' indicating a link
            contract_id_str = col.split()[2]  # Extract contract ID from column name
            try:
                contract_id = int(contract_id_str)
                contract_type = contracts_df.loc[contracts_df['Contract ID'] == contract_id, 'Contract Type'].values[0]
                contract_type_idx = contract_type_indices[contract_type]
                
                sources.append(campaign_id_idx)
                targets.append(contract_type_idx)
                values.append(1)  # You can adjust the value if necessary
            except (ValueError, IndexError):
                continue

# Create links from contract types to contract IDs
for idx, row in contracts_df.iterrows():
    contract_type = row['Contract Type']
    contract_name = row['Contract Name']
    contract_type_idx = contract_type_indices[contract_type]
    contract_id_idx = contract_id_indices[contract_name]
    
    sources.append(contract_type_idx)
    targets.append(contract_id_idx)
    values.append(1)  # You can adjust the value if necessary

# Create the Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Campaign Type -> Campaign ID -> Contract Type -> Contract ID Flow"),
    dcc.Graph(
        id='sankey-graph',
        figure=go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
            )
        )]).update_layout(title_text="Campaign Type -> Campaign ID -> Contract Type -> Contract ID Flow", font_size=10)
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
