from chains import answer_chain


def get_natural_response(question, data, is_limited=False):
    return answer_chain.invoke({
        "question": question,
        "data": data,
        "is_limited": str(is_limited)
    }).strip()
