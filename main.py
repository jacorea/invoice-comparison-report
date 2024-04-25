import streamlit as st
import pandas as pd
import numpy as np
import base64
from pygwalker.api.streamlit import StreamlitRenderer

def main():
    st.set_page_config(layout='wide')
    st.title("Invoice Comparison Report")

    st.write("### Upload CSV File - DHL Orders")
    dhl_orders = st.file_uploader("DHL Orders upload", type=['csv'])
    
    st.write("### Upload Text File - Desktop Shipper Shipped Orders")
    desktop_shipper_orders = st.file_uploader("Desktop Shipper Shipped Orders upload", type=['csv'])
    
    show_prints = st.checkbox('Show Print Statements')
    
    if dhl_orders and desktop_shipper_orders:
        if st.button('Generate Report'):
            updated_dhl_orders = process_dhl_data(dhl_orders, show_prints)
            processed_ds_orders = process_ds_data(desktop_shipper_orders, show_prints)
            merged_data = merge_data(updated_dhl_orders, processed_ds_orders, show_prints)
            
            if merged_data is not None:
                # Download link for merged data
                csv = merged_data.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()  # some strings
                link = f'<a href="data:file/csv;base64,{b64}" download="invoice_comparison_report.csv">Download Merged Data</a>'
                st.markdown(link, unsafe_allow_html=True)
                
                st.write("### PyGwalker UI")
                renderer = StreamlitRenderer(merged_data, spec='./spec/charts.json')
                renderer.explorer()

def process_dhl_data(uploaded_file, show_prints):
    # Define column names based on Excel column indices
    column_names = {
        5: 'orderId',
        11: 'trackingNum1',
        12: 'trackingNumber',
        14: 'address1',
        16: 'city',
        17: 'state',
        18: 'postalCode',
        19: 'country',
        21: 'shippingMethod',
        24: 'weight',
        25: 'weight_unit',
        28: 'pricingZone',
        29: 'dhlPrice',
        30: 'orderId_misplaced',
        64: 'surCharge'
        # Add more column names as needed
    }
    updated_dhl_orders = pd.read_csv(uploaded_file, skiprows=1, header=None, usecols=column_names.keys(), names=column_names.values())
    
    if show_prints:
        st.write('### Before Processing')
        st.write(updated_dhl_orders.head(20))
        st.write(updated_dhl_orders.info())
        st.write(f'Shape before processing: {updated_dhl_orders.shape}')
    
    # REMOVE EMPTY ROWS if weight_unit is blank
    updated_dhl_orders.dropna(subset=['weight_unit'], inplace=True)
    
    # IF ORDERID column is blank fill with orderId_misplaced column
    updated_dhl_orders['orderId'].fillna(updated_dhl_orders['orderId_misplaced'], inplace=True)
    # DROP orderId_misplaced column
    updated_dhl_orders.drop(columns=['orderId_misplaced'], inplace=True)
    
    # if weigh_unit column is equal to "LB" then move values from trackingNum1 column to TrackingNumber column
    updated_dhl_orders['trackingNumber'] = np.where(updated_dhl_orders['weight_unit'] == 'LB', 
                                               updated_dhl_orders['trackingNum1'], 
                                               updated_dhl_orders['trackingNumber'])
    # Make a totalPrice Column: Add dhlPrice + surCharge
    updated_dhl_orders['total_price'] = np.round((updated_dhl_orders['dhlPrice']+updated_dhl_orders['surCharge']),2)
    # CREATE A dhlMarkup(11%): TotalPrice * 1.11
    updated_dhl_orders['dhlMarkup(11%)'] = updated_dhl_orders['total_price']*1.11
    # Create a finalWeight Column: If weight_unit = "LB" then leave as is, if not convert Oz --> Lbs
    updated_dhl_orders['finalWeight'] = np.where(updated_dhl_orders['weight_unit'] == 'OZ', updated_dhl_orders['weight']/16, updated_dhl_orders['weight'])
    # REMOVE WEIGHT AND WEIGHT_UNIT columns
    updated_dhl_orders.drop(columns=['weight', 'weight_unit','trackingNum1'], inplace=True)
    
    if show_prints:
        st.write('### After Processing')
        st.write(updated_dhl_orders.head(20))
        st.write(updated_dhl_orders.info())
        st.write(f'Shape after processing: {updated_dhl_orders.shape}')
    
    return updated_dhl_orders

def process_ds_data(uploaded_file, show_prints):
    # Read the text file as dataframe
    ds_orders = pd.read_csv(uploaded_file)
    
    # Remove double quotes from column names
    column_names = ds_orders.columns.tolist()
    
    # Use subset of columns
    subset_columns = [
        "CreateDate", "TrackingNumber", "SalesChannel", "ItemHeight", "ItemLength", "ItemWidth",
        "ItemWeight", "CartonWeight", "NegotiatedCost", "MarkupCost"
    ]
    ds_orders = ds_orders[subset_columns]

    if show_prints:
        # Check ds orders
        st.write('### Before Processing')
        st.write(ds_orders.head(20))
        st.write(ds_orders.info())
        st.write(f'Shape before processing: {ds_orders.shape}')

    ds_orders.dropna(subset=["CreateDate"], inplace=True)
    
    if show_prints:
        # Check ds orders
        st.write('### After Processing')
        st.write(ds_orders.head(20))
        st.write(ds_orders.info())
        st.write(f'Shape After processing: {ds_orders.shape}')
    
    # Your processing steps for desktop shipper orders
    
    return ds_orders

def merge_data(dhl_data, ds_data, show_prints):
    # Rename 'TrackingNumber' column in ds_orders to match the column name in dhl_orders
    ds_data.rename(columns={"TrackingNumber": "trackingNumber", "SalesChannel": "CUS-ID"}, inplace=True)
    
    # Check if both DataFrames have the 'TrackingNumber' column
    if 'trackingNumber' in dhl_data.columns and 'trackingNumber' in ds_data.columns:
        # Merge dhl_orders and ds_orders based on TrackingNumber
        merged_data = pd.merge(dhl_data, ds_data, on="trackingNumber", how="left")
        
        # Rename columns
        merged_data.rename(columns={"NegotiatedCost": "DhlPrice", "MarkupCost": "VeraCorePrice"}, inplace=True)
        
        # Add 'Profit' column
        merged_data['Profit'] =  merged_data['VeraCorePrice'].astype(float) - merged_data['dhlMarkup(11%)'].astype(float)
        
        if show_prints:
            st.write('### Invoice Comparison Report')
            st.write(merged_data)
            st.write(merged_data.info())
            st.write(f'Shape of Invoice Comparison Report: {merged_data.shape}')
        
        return merged_data
    else:
        st.write("Both DataFrames should have the 'TrackingNumber' column for merging.")

if __name__ == "__main__":
    main()
