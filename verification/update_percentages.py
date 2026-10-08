
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
    
    total_obtained = sum(valid_totals)
    if is_college:
        total_max = sum(valid_max_marks)

        if total_max == 0:
            return None

        percentage = (total_obtained / total_max) * 100

    else:
        total_max = len(valid_totals) * 100
        percentage = (total_obtained / total_max) * 100
    '''
    if is_college:
        total_max = sum(valid_max_marks)
        if total_max == 0:
            return None
        percentage = (sum(valid_totals) / total_max) * 100
    else:
        percentage = (sum(valid_totals) / (len(valid_totals) * 100)) * 100
        
    '''
    # return round(percentage, 2) if not percentage.is_integer() else float(percentage)
    return {
        "total_marks_obtained": total_obtained,
        "total_max_marks": total_max,
        "percentage": (
            round(percentage, 2)
            if not percentage.is_integer()
            else float(percentage)
        ),
    }

def update_records(records):
    """
    Updates percentage only when it is not already extracted
    from the document.

    CGPA and SGPA are NOT calculated here.
    They should be extracted directly from the document.
    """
    for doc_type, docs_list in records.items():
        for doc in docs_list:
            if "marks" in doc and doc["marks"]:
                # doc_type could be 'college' but we check the actual document_type
                is_college = doc.get("document_type") == "college_marksheet"
                result = calculate_percentage(doc["marks"], is_college)
                if result is not None:
                    doc["total_marks_obtained"] = result["total_marks_obtained"]
                    doc["total_max_marks"] = result["total_max_marks"]
                    doc["percentage"] = result["percentage"]
                # perc = calculate_percentage(doc["marks"], is_college)
                # if doc.get("percentage") is None:
                #     perc = calculate_percentage(doc["marks"], is_college)
                #     if perc is not None:
                #         doc["percentage"] = perc
                # if perc is not None:
                #     doc["percentage"] = perc
                #     if is_college:
                #         doc["cgpa"] = round(perc / 10, 2) if not (perc / 10).is_integer() else float(perc / 10)
