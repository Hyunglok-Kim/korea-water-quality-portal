/* Deployment settings. The portal itself is a static site; everything that differs between
   the lab-internal copy and the public one lives here (or in the URL, see below).

   dataBase      where catalog.json, stations.json and the two stores live. A page may override it with
                 ?data=/some/path/ — same-origin paths only, so a link cannot point the map at
                 someone else's files.
   zenodoDoi     the version of the Zenodo record the grids on this site were read from (the Download tab
                 takes the file list itself from catalog.json).
   conceptDoi    the DOI that always resolves to the latest version of the record.
   contactEmail  where questions about the data go.
   paperSection  what "From the paper" on the Explore tab shows:
                   "text"     the plain-words account, with this site's own two charts and the numbers computed
                              from the record's public validation file (data/skill.json). The public setting while
                              the paper is under review: nothing on the page comes from the unpublished manuscript's
                              figures.
                   "figures"  the same, with six figures of the manuscript beside the text. Their files
                              (assets/figures/Fig2,4,5,6,7,8.webp) must then be published with the page; they are
                              kept out of the repository until the lab head decides (see CLAUDE.md).
                   "off"      no such section, and no links to it.
                 A page may override it with ?paper=figures|text|off. */
window.PORTAL_CONFIG = {
  dataBase: "./data/",
  zenodoDoi: "10.5281/zenodo.23750573",
  conceptDoi: "10.5281/zenodo.18502401",
  contactEmail: "hyunglokkim@gist.ac.kr",
  dataContact: "Seongjun Lee (first author) and Hyunglok Kim",
  paperSection: "text",
};
