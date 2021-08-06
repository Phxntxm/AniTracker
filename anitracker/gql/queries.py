media_collection = """
query ($userName: String, $type: MediaType) {
  MediaListCollection (userName: $userName, type: $type) {
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
          id
          season
          seasonYear
          genres
          coverImage {
            large
          }
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
          chapters
          volumes
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
  $mediaId: Int,
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
      mediaId: $mediaId,
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
    {
      deleted
    }
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

search_media = """
query($page:Int,$search:String) {
  Page(page:$page, perPage:50) {
    pageInfo {
      currentPage
      hasNextPage
    }
    media(search:$search) {
      id
      season
      seasonYear
      coverImage {
        large
      }
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
"""
