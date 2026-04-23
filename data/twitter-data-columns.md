**feature**     Description
**id**          A unique, anonymized ID for the Tweet. Referenced by
                response_tweet_id and in_response_to_tweet_id.
**id_author**   A unique, anonymized user ID. @s in the dataset have been
                replaced with their associated anonymized user ID.
**inbound**     Whether the tweet is "inbound" to a company doing customer
                support on Twitter. This feature is useful when re-organizing
                data for training conversational models.
**created_at**  Date and time when the tweet was sent.
**text**        Tweet content. Sensitive information like phone numbers and
                email addresses are replaced with mask values like
                email.response_tweet_id
**response_tweet_id**           IDs of tweets that are responses to this tweet,
                                comma-separated, e.g. "119310,119312"
**in_response_to_tweet_id**     IDs of the tweet this is in response to, if any, e.g. 119313
