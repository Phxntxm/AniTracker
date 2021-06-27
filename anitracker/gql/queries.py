media_collection = """
query ($userName: String) {
  MediaListCollection (userName: $userName, type: ANIME) {
    lists {
      entries {
        id
        mediaId
        status
        score
        notes
        progress
        repeat
        updatedAt
        startedAt {year month day}
        completedAt {year month day}
        media {
          idMal
          season
          seasonYear
          genres
          tags {
            name
            rank
            isMediaSpoiler
          }
          studios {
            edges {
              node {
                name
                isAnimationStudio
              }
            }
          }
          title {
            romaji
            english
            native
            userPreferred
          }
          format
          status
          description
          startDate {year month day}
          endDate {year month day}
          episodes
          averageScore
        }
      }
    }
  }
}
"""

update_entry = """
mutation (
  $id: Int,
  $status: MediaListStatus,
  $score: Float,
  $progress: Int,
  $repeat: Int,
  $notes: String,
  $startedAt: FuzzyDateInput,
  $completedAt: FuzzyDateInput
)
{
  SaveMediaListEntry (
      id: $id,
      status: $status,
      score: $score,
      progress: $progress,
      repeat: $repeat,
      notes: $notes,
      startedAt: $startedAt,
      completedAt: $completedAt
  )
  {
    id
    status
    score
    notes
    progress
    repeat
    updatedAt
    startedAt {year month day}
    completedAt {year month day}
  }
}
"""
delete_entry = """
mutation (
    $id: Int
)
{
    DeleteMediaListEntry (
        id: $id
    )
    {id}
}
"""

viewer = """
{
  Viewer {
    id
    name
  }
}
"""
