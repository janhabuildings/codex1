async function library() {
  try {
    const response=await fetch('/api/dob/status');
    if (!response.ok) throw new Error('Reference status unavailable.');
    const data=await response.json();
    document.querySelector('#library-status').textContent=`${data.documents} documents · ${data.pages} PDF pages · ${data.ocr_pages} OCR pages · ${data.low_text_pages} pages with limited text.`;
  } catch(error) { document.querySelector('#library-status').textContent=error.message; }
}
document.querySelector('#search').addEventListener('submit', async event=>{
  event.preventDefault();
  const status=document.querySelector('#search-status');
  const button=event.target.querySelector('button');button.disabled=true;
  const results=document.querySelector('#results');results.replaceChildren();
  try {
    const params=new URLSearchParams({query:document.querySelector('#query').value,collection:document.querySelector('#collection').value});
    const response=await fetch('/api/dob/search?'+params,{signal:AbortSignal.timeout(20000)});
    if (!response.ok) throw new Error('Search unavailable.');
    const data=await response.json();
    status.textContent=data.excerpts.length?'Showing up to four matching excerpts.':'No matching text found. Try fewer terms; scanned pages may have limited text.';
    for(const hit of data.excerpts){
      const article=document.createElement('article');article.className='chat-message';
      const title=document.createElement('h3');title.textContent=hit.citation;
      const note=document.createElement('p');note.textContent=(hit.ocr_page?'OCR text: verify against PDF. ':'')+(hit.low_text_page?'Limited readable text.':'');
      const text=document.createElement('pre');text.textContent=hit.text;
      const link=document.createElement('a');link.textContent='Open official PDF';
      const url=new URL(hit.source_url);
      if(url.protocol==='https:' && (url.hostname==='nyc.gov'||url.hostname.endsWith('.nyc.gov'))){link.href=url.href;link.target='_blank';link.rel='noopener noreferrer';}
      article.append(title,note,text,link);results.append(article);
    }
  } catch(error){status.textContent=error.message;}
  finally{button.disabled=false;}
});
library();
