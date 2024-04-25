import streamlit as st
import pandas as pd
import numpy as np

def main():
    st.title("Invoice Comparison Report")

    st.write("### Upload CSV File - DHL Orders")
    dhl_orders = st.file_uploader("DHL Orders upload", type=['csv'])
    
    st.write("### Upload Text File - Desktop Shipper Shipped Orders")
    desktop_shipper_orders = st.file_uploader("Desktop Shipper Shipped Orders upload", type=['csv'])
    
    if dhl_orders and desktop_shipper_orders:
        if st.button('Process DHL Orders'):
            processed_dhl_orders = process_dhl_data(dhl_orders)
            st.subheader("Processed DHL Orders")
            st.write(processed_dhl_orders)
        
        if st.button('Process Desktop Shipper Orders'):
            processed_ds_orders = process_ds_data(desktop_shipper_orders)
            st.subheader("Processed Desktop Shipper Orders")
            st.write(processed_ds_orders)

def process_dhl_data(uploaded_file):
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
    
    st.write('### After Processing')
    st.write(updated_dhl_orders.head(20))
    st.write(updated_dhl_orders.info())
    st.write(f'Shape after processing: {updated_dhl_orders.shape}')
    
    return updated_dhl_orders

def process_ds_data(uploaded_file):
    # # Define column names based on Excel column indices
    # column_names = {
    #     'TrackingNumber': 'trackingNumber',
    #     'SalesChannel': 'salesChannel',
    #     'ItemHeight': 'itemHeight',
    #     'ItemLength': 'itemLength',
    #     'ItemWidth': 'itemWidth',
    #     'ItemWeight': 'itemWeight',
    #     'CartonWeight':'cartonWeight',
    #     'NegotiatedCost': 'desktopShipperPrice',
    #     'MarkupCost':'veraCorePrice'
    # }
    # Read the text file as dataframe
    ds_orders = pd.read_csv(uploaded_file)
    
    # Remove double quotes from column names
    column_names = ds_orders.columns.tolist()
    print("Column names:", column_names)
    
    # # Use subset of columns
    subset_columns = [
        "CreateDate", "TrackingNumber", "SalesChannel", "ItemHeight", "ItemLength", "ItemWidth",
        "ItemWeight", "CartonWeight", "NegotiatedCost", "MarkupCost"
    ]
    ds_orders = ds_orders[subset_columns]

        # Check ds orders
    st.write('### Before Processing')
    st.write(ds_orders.head(20))
    st.write(ds_orders.info())
    st.write(f'Shape before processing: {ds_orders.shape}')

    ds_orders.dropna(subset=["CreateDate"], inplace=True)
    
    # Check ds orders
    st.write('### After Processing')
    st.write(ds_orders.head(20))
    st.write(ds_orders.info())
    st.write(f'Shape After processing: {ds_orders.shape}')
    
    # Your processing steps for desktop shipper orders
    
    return ds_orders


if __name__ == "__main__":
    main()
