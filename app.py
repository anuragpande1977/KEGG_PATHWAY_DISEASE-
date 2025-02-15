import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from PIL import Image

def convert_uniprot_to_kegg_gene(uniprot_id):
    """Convert a UniProt ID to a KEGG gene ID."""
    url = f"https://rest.kegg.jp/conv/genes/uniprot:{uniprot_id}"
    response = requests.get(url)
    if response.status_code != 200 or not response.text.strip():
        return None
    return response.text.split("\t")[1].strip()

def get_kegg_pathways(gene_id):
    """Fetch KEGG pathways associated with a given KEGG gene ID."""
    url = f"https://rest.kegg.jp/link/pathway/{gene_id}"
    response = requests.get(url)
    if response.status_code != 200 or not response.text.strip():
        return []
    return [line.split("\t")[1].replace("path:", "") for line in response.text.strip().split("\n")]

def get_kegg_diseases(pathway_id):
    """Fetch disease associations for a given KEGG Pathway ID."""
    url = f"https://rest.kegg.jp/link/disease/path:{pathway_id}"
    response = requests.get(url)
    if response.status_code != 200 or not response.text.strip():
        return []
    data = response.text.strip().split("\n")
    return [line.split("\t")[1].replace("ds:", "") for line in data if line.strip()]

def get_disease_details(disease_id):
    """Fetch disease details from KEGG for a given disease ID."""
    url = f"https://rest.kegg.jp/get/ds:{disease_id}"
    response = requests.get(url)
    if response.status_code == 200:
        lines = response.text.split("\n")
        name = description = ""
        for line in lines:
            if line.startswith("NAME"):
                name = line.split("        ")[-1]
            if line.startswith("DESCRIPTION"):
                description = line.split("        ")[-1]
                break
        return name, description
    return disease_id, "No description available"

def download_kegg_pathway_image(pathway_id):
    """Download high-resolution KEGG pathway image as PNG."""
    url = f"https://rest.kegg.jp/get/{pathway_id}/image"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return None

# Streamlit application starts here
st.title("UniProt to KEGG Pathway and Disease Finder")

# User input for UniProt ID
uniprot_id = st.text_input("Enter UniProt ID (e.g., P01308):")

if st.button("Fetch Details"):
    if uniprot_id:
        st.write(f"**Converting UniProt ID {uniprot_id} to KEGG gene ID...**")
        kegg_gene_id = convert_uniprot_to_kegg_gene(uniprot_id)
        
        if kegg_gene_id:
            st.success(f"**KEGG gene ID:** {kegg_gene_id}")
            
            st.write("**Fetching pathways associated with this gene...**")
            pathways = get_kegg_pathways(kegg_gene_id)
            
            if pathways:
                st.write(f"**Found {len(pathways)} pathway(s). Fetching diseases and images...**")
                disease_data = []
                
                for pathway_id in pathways:
                    diseases = get_kegg_diseases(pathway_id)
                    
                    if diseases:
                        st.write(f"**Pathway {pathway_id} is associated with diseases.**")
                        image_content = download_kegg_pathway_image(pathway_id)
                        if image_content:
                            image = Image.open(BytesIO(image_content))
                            st.image(image, caption=f"Pathway {pathway_id}", use_column_width=True)
                            
                            # Allow the user to download the image
                            st.download_button(
                                label=f"Download {pathway_id}.png",
                                data=image_content,
                                file_name=f"{pathway_id}.png",
                                mime="image/png"
                            )
                    
                    for disease_id in diseases:
                        name, description = get_disease_details(disease_id)
                        disease_data.append([disease_id, name, description])
                
                if disease_data:
                    df = pd.DataFrame(disease_data, columns=["KEGG Disease ID", "Disease Name", "Description"])
                    st.write("### Diseases associated with the UniProt ID:")
                    st.dataframe(df)
                    
                    # Convert dataframe to CSV for download
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Disease Data as CSV",
                        data=csv_data,
                        file_name="UniProt_Disease_Associations.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No diseases found for the associated pathways.")
            else:
                st.error("No pathways found for this gene.")
        else:
            st.error("Conversion failed. Please check the UniProt ID and try again.")
    else:
        st.warning("Please enter a valid UniProt ID.")
