"""
Module Description:
-------------------
Class to extract skills from text and align them to existing taxonomy

Ownership:
----------
Project: LAISER
Owner: GW PSCWP

License:
--------
© 2024 Organization Name. All rights reserved.
Licensed under the XYZ License. You may obtain a copy of the License at
http://www.example.com/license


Input Requirements:
-------------------
- Input files or data formats required by the module.

Output/Return Format:
----------------------------
- Description of the output files or data formats produced by the module.


Revision History:
-----------------
Rev No.     Date            Author              Description
[1.0.0]     05/30/2024      Vedant M.           Initial Version 
[1.0.1]     06/01/2024      Vedant M.           Referencing utils.py and params.py
[1.0.2]     06/08/2024      Satya Phanindra K.  Modify get_aligned_skills function to JSON output


TODO:
-----
- 1: Add references to utils and global parameter file
- 2: sort taxonomy inputs
"""

# native packages

# installed packages
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

# internal packages
from params import DATA_PATH, SKILL_TAXONOMY, SIMILARITY_THRESHOLD
from utils import Utils


class Skill_Extractor:
    """
    Class to extract skills from text and align them to existing taxonomy

    ...

    Attributes
    ----------
    taxonomy : text
        Name of reference skill database/taxonomy

    nlp : spacy nlp model
        Short description

    db : file object 
        contains skill information from taxonomy

    ner_extractor: SkillNER object
        extractor object initialised with NLP, PhraseMatcher and Skill DB

    Parameters
    ----------
    taxonomy : text, optional
        Name of reference skill database/taxonomy
        Available Taxonomy are LIGHTCAST, ESCO, defaults to 'LIGHTCAST'
        
    Methods
    -------
    extract(input_text: text)
        The function extracts skills from text using NER model

    get_aligned_skills(skills: list, output_taxonomy = 'OSN'):
        This function aligns the skills provided to the desired taxonomy
    ....

    """

    def __init__(self, taxonomy='LIGHTCAST'):
        """
        Class constructor

        Parameters
        ----------
        taxonomy : text, optional
            Name of reference skill database/taxonomy
            Available Taxonomy are LIGHTCAST, ESCO, defaults to 'LIGHTCAST'
        """
        # Initialization of objects here
        self.taxonomy = taxonomy
        self.nlp = spacy.load("en_core_web_lg")

        self.db = None
        if taxonomy == 'LIGHTCAST':
            self.db = SKILL_DB
        else:
            self.db = SKILL_TAXONOMY

        self.ner_extractor = SkillExtractor(self.nlp, self.db, PhraseMatcher)

        return

    def extract(self, input_text):
        """
        The function extracts skills from text using NER model

        Parameters
        ----------
        input_text : text
            Job advertisement / Job Description / Syllabus Description / Course Outcomes etc.

        Returns
        -------
        list: List of extracted skills from text


        Notes
        -----
            The Function is designed only to return list of skills based on selected taxonomy database.
            The output might change if the taxonomy parameter of the class is provided with different input.

        """
        # Function implementation here

        extracted_skills_set = set()
        annotations = None
        try:
            annotations = self.ner_extractor.annotate(input_text)
        except ValueError as e:
            print(f"Skipping example, ValueError encountered: {e}")
        except Exception as e:
            print(f"Skipping example, An unexpected error occurred: {e}")

        # for item in annotations['results']['full_matches']:
        #     extracted_skills_set.add(item['doc_node_value'])

        # get ngram_scored
        for item in annotations['results']['ngram_scored']:
            extracted_skills_set.add(item['doc_node_value'])

        return list(extracted_skills_set)

    def get_aligned_skills(self, skills, output_taxonomy='OSN'):
        """
        This function aligns the skills provided to the desired taxonomy
    
        Parameters
        ----------
        skills : list
            Provide list of skill extracted from Job Descriptions / Syllabus.
    
        output_taxonomy : text, optional
            Name of output skill database/taxonomy
            Available Taxonomy are LIGHTCAST, ESCO, OSN defaults to 'OSN'
    
        Returns
        -------
        list: List of taxonomy skills from text in JSON format
            [
                {
                    "SkillName": "Skill1",
                    "SkillID": "ID1",
                    "corr_coeff": similarity_score
                },
                ...
            ]
    
        """
        if output_taxonomy == 'OSN':
            osn_comp_df = pd.read_csv(DATA_PATH + "osn_comp_prepped.csv")
            osn_pub_df = pd.read_csv(DATA_PATH + "osn_pr_prepped.csv")
            osn_ind_df = pd.read_csv(DATA_PATH + "osn_ind_prepped.csv")
            osn = pd.concat([osn_comp_df, osn_pub_df, osn_ind_df], ignore_index=True)
            key_series = osn[["RSD Name", "ID"]]
        else:
            skill_df = pd.read_json(DATA_PATH + 'skill_db_relax_20.json').T
            key_series = skill_df[['skill_name', 'id']].reset_index().drop(['index'], axis=1)
    
        # Initialize an empty set to track previously matched skills
        matched_skills_set = set()
        # Create an empty list for the skills that match
        skill_matches = []
        nlp = self.nlp
        utils = Utils(nlp)
    
        # Iterate through each skill in extracted_skills_list
        for extracted_skill in skills:
            # Check if extracted_skill contains non-whitespace characters
            if extracted_skill.strip():
                # Calculate GloVe embedding for the extracted skill
                extracted_embedding = utils.get_embedding(extracted_skill)
    
                # Initialize variables to store the best match and its similarity score
                best_match = None
                best_similarity = 0.0
    
                # Iterate through each keyword in key_series (skills from taxonomy)
                for index, row in key_series.iterrows():
                    key_skill, key_id = row["RSD Name"], row["ID"]
                    # Calculate embedding for the keywords/skills from taxonomy
                    key_embedding = utils.get_embedding(key_skill)
    
                    # Calculate cosine similarity between extracted skill and keyword skill
                    similarity = utils.cosine_similarity(extracted_embedding, key_embedding)
    
                    # If the similarity score is above the threshold and the skill is not already matched
                    if similarity >= SIMILARITY_THRESHOLD and key_skill not in matched_skills_set:
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = key_skill
                            best_id = key_id
    
                        # Update the set of previously matched skills
                        matched_skills_set.add(key_skill)
    
                # If best match was found, add it to the list of matched skills
                if best_match:
                    skill_matches.append({
                        "SkillName": best_match,
                        "SkillID": best_id,
                        "corr_coeff": best_similarity
                    })
    
        return skill_matches