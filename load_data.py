import jnius_config;
jnius_config.add_classpath('jedai-core-3.2.1-jar-with-dependencies.jar')

from jnius import autoclass
import pandas as pd


# java object type
EntitySerializationReader = autoclass('org.scify.jedai.datareader.entityreader.EntitySerializationReader')
GtSerializationReader = autoclass('org.scify.jedai.datareader.groundtruthreader.GtSerializationReader')
List = autoclass('java.util.List')
EntityProfile = autoclass('org.scify.jedai.datamodel.EntityProfile')
Attribute = autoclass('org.scify.jedai.datamodel.Attribute')
IdDuplicates = autoclass('org.scify.jedai.datamodel.IdDuplicates')


def parse_entity_to_dataframe(file_path):
    df = pd.DataFrame()
    
    serializationReader = EntitySerializationReader(file_path)
    profiles = serializationReader.getEntityProfiles()
    profilesIterator = profiles.iterator()
    profile_index = 0
    while profilesIterator.hasNext() :
        # init new row
        row = {}

        # build row's data
        profile = profilesIterator.next()
        row['url'] = profile.getEntityUrl()
        attributesIterator = profile.getAttributes().iterator()
        while attributesIterator.hasNext():
            attribute = attributesIterator.next()
            row[attribute.name] = attribute.value
        
        # add to df
        df = pd.concat([df, pd.DataFrame(row, index=[profile_index])])
        profile_index += 1

    return df, profiles

def parse_ground_truth_to_dataframe(file_path, names = ['profile_1', 'profile_2']):
    df = pd.DataFrame()
    
    serializationReader = GtSerializationReader(file_path)
    idDuplicates = serializationReader.getDuplicatePairs(None, None)
    idDuplicatesIterator = idDuplicates.iterator()
    idDuplicates_index = 0

    while idDuplicatesIterator.hasNext() :
        # init new row
        row = {}

        # build row's data
        idDuplicate = idDuplicatesIterator.next()
        row[names[0]] = idDuplicate.entityId1
        row[names[1]] = idDuplicate.entityId2
        
        # add to df
        df = pd.concat([df, pd.DataFrame(row, index=[idDuplicates_index])])
        idDuplicates_index += 1

    return df, idDuplicates