import json
import os
import glob

def calculate_percentage(marks, is_college=False):
    if not marks:
        return None
        
    valid_totals = []
    valid_max_marks = []
    for subject, details in marks.items():
        total = details.get("total")
        if total is not None:
            valid_totals.append(total)
            if is_college:
                max_m = details.get("max_marks")
                valid_max_marks.append(max_m if max_m is not None else 100)
            
    if not valid_totals:
        return None
        
    if is_college:
        total_max = sum(valid_max_marks)
        if total_max == 0:
            return None
        percentage = (sum(valid_totals) / total_max) * 100
    else:
        percentage = (sum(valid_totals) / (len(valid_totals) * 100)) * 100
        
    return round(percentage, 2) if not percentage.is_integer() else float(percentage)

def update_records(records):
    """
    Updates the percentages and cgpa directly in the records dictionary
    before it is saved by the main pipeline.
    """
    for doc_type, docs_list in records.items():
        for doc in docs_list:
            if "marks" in doc and doc["marks"]:
                # doc_type could be 'college' but we check the actual document_type
                is_college = doc.get("document_type") == "college_marksheet"
                perc = calculate_percentage(doc["marks"], is_college)
                if perc is not None:
                    doc["percentage"] = perc
                    if is_college:
                        doc["cgpa"] = round(perc / 10, 2) if not (perc / 10).is_integer() else float(perc / 10)

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    modified = False
    
    if "documents" in data:
        # Instead of duplicating, we can just call our new function
        # Data["documents"] has the same structure as `records`
        update_records(data["documents"])
        modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
if __name__ == "__main__":
    search_path = os.path.join(r"d:\NIC\docAI\output", "*.json")
    for filepath in glob.glob(search_path):
        process_file(filepath)
