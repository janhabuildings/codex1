async function library() {
  try {
    const response=await fetch('/api/dob/status');
    if (!response.ok) throw new Error('Reference status unavailable.');
    const data=await response.json();
    document.querySelector('#library-status').textContent=`${data.dob_documents} DOB PDFs + Zoning Resolution (${data.zoning_pages} pages) · ${data.pages} total PDF pages · ${data.ocr_pages} OCR pages · ${data.low_text_pages} pages with limited text.`;
  } catch(error) { document.querySelector('#library-status').textContent=error.message; }
}
let activeSearch=null, nextPage=0, busy=false;
const more=document.querySelector('#show-more');
async function loadPage(){
  if(busy || !activeSearch) return;
  busy=true;
  const status=document.querySelector('#search-status');
  const button=document.querySelector('#search button');button.disabled=true;more.disabled=true;
  const results=document.querySelector('#results');
  try {
    const params=new URLSearchParams({...activeSearch,page:nextPage});
    const response=await fetch('/api/dob/search?'+params,{signal:AbortSignal.timeout(20000)});
    const data=await response.json();
    if (!response.ok) throw new Error(data.error || 'Search unavailable.');
    nextPage=data.next_page;more.hidden=!data.has_more;
    for(const hit of data.excerpts){
      const article=document.createElement('article');article.className='chat-message';
      const title=document.createElement('h3');title.textContent=(hit.collection==='zoning-resolution'?'Zoning Resolution — ':'')+hit.citation;
      const note=document.createElement('p');note.textContent=(hit.ocr_page?'OCR text: verify against PDF. ':'')+(hit.low_text_page?'Limited readable text.':'');
      const text=document.createElement('pre');text.textContent=hit.text;
      article.append(title,note,text);
      if(hit.source_url){
        const url=new URL(hit.source_url);
        if(url.protocol==='https:' && (url.hostname==='nyc.gov'||url.hostname.endsWith('.nyc.gov'))){
          const link=document.createElement('a');link.textContent='Open official PDF';link.href=url.href;link.target='_blank';link.rel='noopener noreferrer';article.append(link);
        }
      } else if(hit.source_note){
        const source=document.createElement('p');source.textContent=hit.source_note;article.append(source);
      }
      results.append(article);
    }
    status.textContent=results.children.length ? `Showing ${results.children.length} excerpts.${data.has_more?' More results are available.':' End of matching results.'}` : 'No matching text found. Try fewer terms; scanned pages may have limited text.';
  } catch(error){status.textContent=error.message;}
  finally{button.disabled=false;more.disabled=false;busy=false;}
}
document.querySelector('#search').addEventListener('submit',event=>{
  event.preventDefault();if(busy)return;
  activeSearch={query:document.querySelector('#query').value,collection:document.querySelector('#collection').value};
  nextPage=0;more.hidden=true;document.querySelector('#results').replaceChildren();loadPage();
});
more.addEventListener('click',()=>loadPage());
library();
