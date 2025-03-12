import argparse
import csv
import re
from typing import List, Dict, Any
from Bio import Entrez
import os

# Set Entrez email
Entrez.email = os.getenv("ENTREZ_EMAIL", "your-email@example.com")

# Heuristic keywords to filter non-academic authors
NON_ACADEMIC_KEYWORDS = ["Pharma", "Biotech", "Inc", "Ltd", "Corporation", "Company", "Laboratories"]
ACADEMIC_KEYWORDS = ["University", "Institute", "Academy", "Hospital", "Research Center"]

def fetch_papers(query: str) -> List[Dict[str, Any]]:
    handle = Entrez.esearch(db="pubmed", term=query, retmax=20)
    record = Entrez.read(handle)
    handle.close()
    pmids = record.get("IdList", [])
    
    results = []
    for pmid in pmids:
        paper_data = extract_paper_details(pmid)
        if paper_data:
            results.append(paper_data)
    return results

def extract_paper_details(pmid: str) -> Dict[str, Any]:
    handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
    records = Entrez.read(handle)
    handle.close()
    
    paper_info = {"PubmedID": pmid, "Title": "", "Publication Date": "", "Non-academic Author(s)": [], "Company Affiliation(s)": [], "Corresponding Author Email": ""}
    
    try:
        article = records["PubmedArticle"][0]["MedlineCitation"]["Article"]
        paper_info["Title"] = article["ArticleTitle"]
        paper_info["Publication Date"] = article["Journal"]["JournalIssue"]["PubDate"]["Year"]
        authors = article.get("AuthorList", [])

        for author in authors:
            if "AffiliationInfo" in author:
                affiliation = author["AffiliationInfo"][0]["Affiliation"]
                if any(keyword in affiliation for keyword in NON_ACADEMIC_KEYWORDS) and not any(keyword in affiliation for keyword in ACADEMIC_KEYWORDS):
                    paper_info["Non-academic Author(s)"].append(author["LastName"] + " " + author["ForeName"])
                    paper_info["Company Affiliation(s)"].append(affiliation)
                
                if "@" in affiliation:
                    email_match = re.search(r"[\w\.-]+@[\w\.-]+", affiliation)
                    if email_match:
                        paper_info["Corresponding Author Email"] = email_match.group()
    except Exception:
        pass
    
    return paper_info if paper_info["Non-academic Author(s)"] else None

def save_to_csv(data: List[Dict[str, Any]], filename: str):
    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["PubmedID", "Title", "Publication Date", "Non-academic Author(s)", "Company Affiliation(s)", "Corresponding Author Email"])
        writer.writeheader()
        writer.writerows(data)

def main():
    parser = argparse.ArgumentParser(description="Fetch research papers with non-academic authors from PubMed.")
    parser.add_argument("query", type=str, help="Search query for PubMed.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument("-f", "--file", type=str, help="Output CSV file name.")
    args = parser.parse_args()

    if args.debug:
        print("Fetching papers for query:", args.query)
    
    papers = fetch_papers(args.query)
    
    if args.file:
        save_to_csv(papers, args.file)
        print(f"Results saved to {args.file}")
    else:
        print(papers)

if __name__ == "__main__":
    main()
