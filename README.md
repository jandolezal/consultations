# Scrape feedback to EC consultations

European Commission gathers feedback from stakeholders on various policies through [Have your say](https://ec.europa.eu/info/law/better-regulation/have-your-say) website.

I did not find a section with basic statistics on received feedback (like organization type, country of the respondent etc.) for a particular consultation.

These scripts parse the received feedback within a consultation based on url where you can get a JSON response and id of the consultation.

Only first attachment to the feedback (e.g. pdf file) is taken into account.
