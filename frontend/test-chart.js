// test-chart.js
import { renderToString } from '@vue/server-renderer';
import { createSSRApp, h } from 'vue';
import OrganizationChart from 'primevue/organizationchart';

const App = {
    components: { OrganizationChart },
    data() {
        return {
            data: {
                key: '0',
                label: 'Argentina',
                type: 'person'
            }
        };
    },
    template: `
    <OrganizationChart :value="data">
      <template #person="slotProps">
        <div>{{ slotProps.node.label }}, {{ slotProps.node.data.formula }}</div>
      </template>
    </OrganizationChart>
  `
};

const app = createSSRApp(App);
app.use(OrganizationChart);

renderToString(app).then(html => {
    console.log("RENDERED HTML:", html);
}).catch(err => {
    console.error("ERROR:", err);
});
